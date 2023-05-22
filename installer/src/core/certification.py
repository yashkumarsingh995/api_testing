import json
import logging
import requests
import os
import boto3

from aws_lambda_powertools.utilities.typing import LambdaContext
from bs4 import BeautifulSoup
from datetime import datetime
from rctools.alerts import create_certification_approved_alert, create_certification_rejected_alert, add_user_alert
from rctools.installers import update_installer_data_in_s3, get_installer_data_from_s3
from rctools.models import ReadiChargeBaseModel
from typing import Optional, Dict


ALERTS_TABLE = os.environ.get('ALERTS_TABLE')
TIMEOUT_SECONDS = 10
USER_DATA_BUCKET = os.environ.get('USER_DATA_BUCKET')

logger = logging.getLogger()
logger.setLevel(logging.INFO)
dynamodb = boto3.resource('dynamodb')
s3_client = boto3.client('s3')

alerts_table = dynamodb.Table(ALERTS_TABLE)


class CertificationResponse(ReadiChargeBaseModel):
    error: Optional[bool]  # was there an error
    manual_link: Optional[str]
    verifiable: Optional[bool]  # did we attempt to verify (e.g. is there code present to attempt verification)
    verified: Optional[bool]  # was it verified

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.error = False
        self.verifiable = False
        self.verified = False


def verify_certification(event: Dict[str, any], context: LambdaContext) -> bool:
    logger.info(f'Received installer certification request {event["Records"]}')
    for record in event['Records']:
        payload = json.loads(record['body'])

        state = payload['state'].lower()
        if state == 'or':
            state = 'oregon'  # can't call a function "or"
        license_num = payload['license_num']
        installer_id = payload['installer_id']
        logger.info(f'Running certification check for {installer_id} in {license_num}')

        resp = CertificationResponse()
        certifier = StateCertifications()
        cert_fn = getattr(certifier, state, None)
        logger.info(f'Running for state {state}')
        if callable(cert_fn):
            # Create default rejected alert
            alert = create_certification_rejected_alert(installer_id)
            try:
                result = cert_fn(license_num)
                resp.verified = result.valid
                resp.verifiable = result.verifiable
                if result.valid:
                    # Replace with approved alert
                    alert = create_certification_approved_alert(installer_id)
                if result.manual_link:
                    resp.manual_link = result.manual_link
                    logger.info(f'Returning manual link {resp.manual_link}')
                logger.info(f'Certification came back {resp.verified}')
            except:
                resp.error = True
                logger.exception(f'Certification ran into an error, could not be verified')
            # Send alert
            add_user_alert(alerts_table, installer_id, alert)
            # And update user data
            data = get_installer_data_from_s3(s3_client, USER_DATA_BUCKET, installer_id)
            update = {'license': {**data.get('license', {}), **resp.dict()}}
            logger.info(f'Updating user data with {update}')
            update_installer_data_in_s3(s3_client, USER_DATA_BUCKET, installer_id, update)
        else:
            logger.warning('No certification function found')
    return True


class StateCertifications:
    class Response(ReadiChargeBaseModel):
        business_name: Optional[str]
        contact_info: Optional[str]
        issue_date: Optional[str]
        expiry_date: Optional[str]
        manual_link: Optional[str]
        status: Optional[str]
        valid: Optional[bool]
        verifiable: Optional[bool]  # do we have code to attempt to verify

        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.valid = False
            self.verifiable = True

    def az(self, license_num='') -> Response:
        resp = StateCertifications.Response()
        # XXX looks very complicated and doubtful
        resp.manual_link = 'https://azroc.my.site.com/AZRoc/s/contractor-search'
        resp.verifiable = False
        return resp

    def ca(self, license_num='1081623') -> Response:
        resp = StateCertifications.Response()
        html = requests.get(f'https://www.cslb.ca.gov/OnlineServices/CheckLicenseII/LicenseDetail.aspx?LicNum={license_num}', timeout=TIMEOUT_SECONDS)
        soup = BeautifulSoup(html.text, 'html.parser')
        # Parse HTML
        resp.business_name = soup.find(id='MainContent_BusInfo').get_text()
        resp.issue_date = soup.find(id='MainContent_IssDt').get_text()
        resp.expiry_date = soup.find(id='MainContent_ExpDt').get_text()
        resp.status = soup.find(id='MainContent_Status').get_text()
        if 'This license is current and active.' in resp.status:
            resp.valid = True
        return resp

    def co(self, license_num='') -> Response:
        resp = StateCertifications.Response()
        # XXX another ASP.net site
        resp.manual_link = 'https://apps.colorado.gov/dora/licensing/Lookup/LicenseLookup.aspx'
        resp.verifiable = False
        return resp

    def fl(self, license_num='EC13001983') -> Response:
        resp = StateCertifications.Response()
        body = {
            'hSearchType': 'LicNbr',
            'hDivision': 'ALL',
            'hBoard': '08',
            'hLicNbr': license_num,
            'hRecsPerPage':	'10',
            'LicNbr': license_num,
            'Board': '08',
            'LicenseType': '%A0',
            'RecsPerPage': '10',
            'Search1': 'Search'
        }
        html = requests.post(f'https://www.myfloridalicense.com/wl11.asp?mode=2&search=LicNbr&SID=&brd=&typ=', body, timeout=TIMEOUT_SECONDS)
        soup = BeautifulSoup(html.text, 'html.parser')

        for row in soup.find('form').find('table').find('table').find('table').findAll('tr'):
            text = str(row)
            # Find the Primary business row from the results page
            if 'Primary' in text and 'LicenseDetail' in text:
                link = row.find('a')['href']
                # Jump to the results link
                results_html = requests.get(f'https://www.myfloridalicense.com/{link}')
                results_soup = BeautifulSoup(results_html.text, 'html.parser')
                # Then find the License Information table
                for b in results_soup.findAll('b'):
                    if license_num in b.get_text():
                        parent_table = b.find_parent('table')
                        for tr in parent_table.findAll('tr'):
                            if 'Licensure Date' in tr.get_text():
                                resp.issue_date = tr.findAll('td')[-1].get_text()
                            elif 'Expires' in tr.get_text():
                                resp.expiry_date = tr.findAll('td')[-1].get_text()
                            elif 'Status' in tr.get_text():
                                resp.status = tr.findAll('td')[-1].get_text()
                                if 'Current,Active' in resp.status:
                                    resp.valid = True
                break
        return resp

    def il(self, license_num='') -> Response:
        resp = StateCertifications.Response()
        # XXX cook county or Chicago specific
        resp.manual_link = 'https://webapps1.chicago.gov/activeecWeb/'
        resp.verifiable = False
        return resp

    def ga(self, license_num='EN217244') -> Response:
        resp = StateCertifications.Response()
        # XXX ASP site
        resp.manual_link = 'https://verify.sos.ga.gov/verification/'
        resp.verifiable = False
        return resp

    def ha(self, license_num='CT-37054') -> Response:
        resp = StateCertifications.Response()
        # XXX protected WP API
        # html = requests.get('https://mypvl.dcca.hawaii.gov/wp-json/pvlsc/v1/get_list')
        # soup = BeautifulSoup(html.text, 'html.parser')
        # nonce_node = soup.find(text='pvlsc_nonce=')
        # print(nonce_node)
        # nonce_text = nonce_node.get_text()
        # nonce = nonce_text[nonce_text.find('var pvlsc_nonce="') + 1: nonce_text.find('";')]
    
        # html = requests.post(
        #     'https://mypvl.dcca.hawaii.gov/wp-json/pvlsc/v1/get_list',
        #     data={
        #         'module': "License",
        #         'where'	"(((Name+=+'CT-37054'+OR+Name+=+'CT-37054-0')))+AND+JointVenture__c+=+false"
        #         'fields': ["Id", "Name", "Licensee__r.Name", "LicenseTypeDescription__c", "BusinessStreet__c", "BusinessCity__c", "BusinessState__c", "BusinessZipCode__c"],
        #         '_wpnonce': nonce,
        #         'limit': "10000000"
        #     },
        #     timeout=TIMEOUT_SECONDS
        # )
        # soup = BeautifulSoup(html.text, 'html.parser')
        # print({
        #         'module': "License",
        #         'where'	"(((Name+=+'CT-37054'+OR+Name+=+'CT-37054-0')))+AND+JointVenture__c+=+false"
        #         'fields': ["Id", "Name", "Licensee__r.Name", "LicenseTypeDescription__c", "BusinessStreet__c", "BusinessCity__c", "BusinessState__c", "BusinessZipCode__c"],
        #         '_wpnonce': nonce,
        #         'limit': "10000000"
        #     })
        # print(html.status_code)
        # print(html.text)
        resp.manual_link = 'https://mypvl.dcca.hawaii.gov/public-license-search/'
        resp.verifiable = False
        return resp

    def ma(self, license_num="22415") -> Response:
        resp = StateCertifications.Response()
        # html = requests.get(f'https://aca-prod.accela.com/LARA/GeneralProperty/LicenseeDetail.aspx?LicenseeNumber={license_num}&LicenseeType=Electrical+Contractor', timeout=TIMEOUT_SECONDS)
        # soup = BeautifulSoup(html.text, 'html.parser')

        # aspx_fields = ('__EVENTARGUMENT', '__VIEWSTATE', '__VIEWSTATEGENERATOR', 'ACA_CS_FIELD', '__VIEWSTATEENCRYPTED')
        # data = {
        #     'ctl00$ScriptManager1': "ctl00$PlaceHolderMain$updatePanel|ctl00$PlaceHolderMain$btnNewSearch",
        #     'ctl00$HeaderNavigation$hdnShoppingCartItemNumber': "",
        #     'ctl00$HeaderNavigation$hdnShowReportLink': "N",
        #     'ctl00$PlaceHolderMain$refLicenseeSearchForm$ddlLicensingBoard': "Board of State Examiners of Electricians",
        #     'ctl00$PlaceHolderMain$refLicenseeSearchForm$ddlLicenseType': "",
        #     'ctl00$PlaceHolderMain$refLicenseeSearchForm$txtLicenseNumber': license_num,
        #     'ctl00$PlaceHolderMain$refLicenseeSearchForm$txtFirstName': "",
        #     'ctl00$PlaceHolderMain$refLicenseeSearchForm$txtMiddleInitial': "",
        #     'ctl00$PlaceHolderMain$refLicenseeSearchForm$txtLastName': "",
        #     'ctl00$PlaceHolderMain$refLicenseeSearchForm$txtBusiName': "",
        #     "ctl00$PlaceHolderMain$refLicenseeSearchForm$txtBusiName2": "",
        #     'ctl00$PlaceHolderMain$refLicenseeSearchForm$txtCity': "",
        #     'ctl00$PlaceHolderMain$refLicenseeSearchForm$txtState$State1': "",
        #     'ctl00$PlaceHolderMain$refLicenseeSearchForm$txtZipCode': "",
        #     'ctl00$PlaceHolderMain$refLicenseeSearchForm$txtZipCode_ZipFromAA': "0",
        #     'ctl00$PlaceHolderMain$refLicenseeSearchForm$txtZipCode_zipMask': "",
        #     'ctl00$PlaceHolderMain$refLicenseeSearchForm$txtZipCode_ext_ClientState': "",
        #     'ctl00$HDExpressionParam': "",
        #     'Submit': "Submit",
        #     '__EVENTTARGET': 'ctl00$PlaceHolderMain$btnNewSearch',
        #     '__ASYNCPOST': 'true'
        # }

        # form = soup.find(id='aspnetForm')
        # for id in aspx_fields:
        #     data[id] = form.find(id=id).get('value') if form.find(id=id) else ""

        # # for k,v in data.items():
        # #     print(f'{k}: {v}')
        # r = requests.post(
        #     'https://elicensing21.mass.gov/CitizenAccess/GeneralProperty/PropertyLookUp.aspx?isLicensee=Y', 
        #     data=data,
        #     headers={
        #         'Cookie': 'AWSALB=W2hQWLcgJZfU6hWw3wbECWe9b8OtBCr1ykLZ9HNfQOvx6pw+15L6Mwp5q4uHXI5LG9kUw3rpU6x7ilhtoJfLxX7TXxWRdUw99oTOYS79p/tssQzo5VNgkDGO4UCL; AWSALBCORS=W2hQWLcgJZfU6hWw3wbECWe9b8OtBCr1ykLZ9HNfQOvx6pw+15L6Mwp5q4uHXI5LG9kUw3rpU6x7ilhtoJfLxX7TXxWRdUw99oTOYS79p/tssQzo5VNgkDGO4UCL; LASTEST_REQUEST_TIME=1668700771821; .ASPXANONYMOUS=IeV4SluLPN2rn81IYfivW00ZS8b7j_Yalk8mMvM5xxpRSua6C8_bxThbkI4llKKP3C6sy2aFVDZryjsv94feplD6s6rCj_ypc42WwKVAoeohErKEyWig6AtUSxxuJfb-yet8MdS_B3K-Z50L7E5P8srFOddQTZXknIszUsrHLSuEJlMda6YO_VSHdib0Y-9I0; ACA_SS_STORE=3ydesjltpne3lkbqljgtlej2; ACA_USER_PREFERRED_CULTURE=en-US; ACA_COOKIE_SUPPORT_ACCESSSIBILITY=False; ACA_CS_KEY=bff9ff2ab4b7470997ecf7d02c87b33f',
        #         'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8',
        #         'X-MicrosoftAjax': 'Delta=true',
        #         'X-Requested-With': 'XMLHttpRequest'
        #     })
        # # print(data)
        # print(r.status_code)
        # print(r.content)
        resp.manual_link = 'https://elicensing21.mass.gov/CitizenAccess/GeneralProperty/PropertyLookUp.aspx?isLicensee=Y'
        resp.verifiable = False
        return resp

    def md(self, license_num='15411') -> Response:
        resp = StateCertifications.Response()
        html = requests.post(
            'https://www.dllr.state.md.us/cgi-bin/ElectronicLicensing/OP_Search/OP_search.cgi',
            data={
                'calling_app': "ME::ME_registration_num",
                'search_page': "ME::ME_registration_num",
                'from_self': "true",
                'unit': "19",
                'html_title': "Master+Electricians",
                'error_contact': "Division+of+Occupational+and+Professional+Licensing",
                'reg': license_num,
                'Submit': "Search"
            },
            timeout=TIMEOUT_SECONDS)
        soup = BeautifulSoup(html.text, 'html.parser')
        
        results = soup.find('table')
        rows = results.find('tbody').find_all('tr')
        if len(rows) == 1:
            resp.valid = False
            return resp
        result_row = rows[1]
        cells = result_row.find_all('td')

        resp.business_name = cells[0].get_text()        
        resp.expiry_date = cells[5].get_text()
        resp.status = cells[7].get_text()
        resp.valid = True  # expired or invalid licenses won't show
        return resp

    def mi(self, license_num='6101375') -> Response:
        resp = StateCertifications.Response()
        html = requests.get(f'https://aca-prod.accela.com/LARA/GeneralProperty/LicenseeDetail.aspx?LicenseeNumber={license_num}&LicenseeType=Electrical+Contractor', timeout=TIMEOUT_SECONDS)
        soup = BeautifulSoup(html.text, 'html.parser')

        resp.business_name = soup.find(id='ctl00_PlaceHolderMain_licenseeGeneralInfo_lblLicenseeBusinessName_value').get_text()
        resp.contact_info = soup.find(id='ctl00_PlaceHolderMain_licenseeGeneralInfo_lblContactName_value').get_text()
        resp.issue_date = soup.find(id='ctl00_PlaceHolderMain_licenseeGeneralInfo_lblLicenseIssueDate_value').get_text()
        resp.expiry_date = soup.find(id='ctl00_PlaceHolderMain_licenseeGeneralInfo_lblExpirationDate_value').get_text()
        resp.status = soup.find(id='ctl00_PlaceHolderMain_licenseeGeneralInfo_lblBusinessName2_value').get_text()
        if resp.status == 'Issued':
            resp.valid = True
        return resp

    def nc(self, license_num='11585') -> Response:
        """Currently, we are assuming all NC licenses are the Unlimited Classification License types"""
        resp = StateCertifications.Response()
        html = requests.post(
            'https://arls-public.ncbeec.org/Public/_Search/',
            data={
                'AccountTypeID': "20",
                'AccountDefinitionIdnt': "154",
                'AccountNumber': license_num.replace('U.', ''),  # don't include unlimited classification types prefix, if provided
                'CompanyName': "",
                'FirstName': "",
                'LastName': "",
                'PhoneNumber': "",
                'streetAddress': "",
                'PostalCode': "",
                'City': "",
                'StateCode': ""
            },
            timeout=TIMEOUT_SECONDS
        )
        soup = BeautifulSoup(html.text, 'html.parser')
        result = soup.find('a')
        onclick = result['onclick']
        id = onclick[onclick.find('(') + 1:onclick.find(')')]

        # Then do a GET with the ID found above
        html = requests.get(f'https://arls-public.ncbeec.org/Public/_ShowAccountDetails/{id}?Source=Search')
        soup = BeautifulSoup(html.text, 'html.parser')

        data = {}
        fieldsets = soup.find_all('fieldset')
        results = fieldsets[1]
        labels = results.find_all(class_='display-label')
        fields = results.find_all(class_='display-field')
        for idx, l in enumerate(labels):
            data[l.get_text()] = fields[idx].get_text()

        resp.issue_date = data.get('Effective Date')
        resp.expiry_date = data.get('Expiration Date')
        resp.status = data.get('Status').replace('\r\n', '').replace(' ', '')
        if resp.status == 'Active':
            resp.valid = True
        return resp

    def nj(self, license_num='34EI01574400') -> Response:
        resp = StateCertifications.Response()
        # initial_html = requests.get('https://newjersey.mylicense.com/verification/Search.aspx', timeout=TIMEOUT_SECONDS)
        # initial_soup = BeautifulSoup(initial_html.text, 'html.parser')
        # form = initial_soup.find(id='TheForm')
        # inputs = form.find_all('input', type='hidden')
        # body = {
        #     't_web_lookup__profession_name': "",
        #     't_web_lookup__license_type_name': "Electrical+Contractor",
        #     't_web_lookup__first_name': "",
        #     't_web_lookup__last_name': "",
        #     't_web_lookup__license_no': license_num,
        #     't_web_lookup__addr_city': "",
        #     'sch_button': "Search"
        # }
        # for i in inputs:
        #     body[i['name']] = i['value']
        # XXX search results are always empty, but does not say "invalid"
        # html = requests.post('https://newjersey.mylicense.com/verification/Search.aspx', body, cookies=initial_html.cookies, timeout=TIMEOUT_SECONDS)
        # print(html.text)
        resp.manual_link = 'https://newjersey.mylicense.com/verification/Search.aspx'
        resp.verifiable = False
        return resp

    def nv(self, license_num='0076191') -> Response:
        resp = StateCertifications.Response()
        # XXX ASP site
        resp.manual_link = 'https://app.nvcontractorsboard.com/Clients/NVSCB/Public/ContractorLicenseSearch/ContractorLicenseSearch.aspx'
        resp.verifiable = False
        return resp

    def ny(self, license_num='012711') -> Response:
        resp = StateCertifications.Response()
        html = requests.get(f'https://a810-bisweb.nyc.gov/bisweb/LicenseQueryServlet?licno={license_num}&licensetype=A', timeout=TIMEOUT_SECONDS)
        soup = BeautifulSoup(html.text, 'html.parser')
        tables = soup.findAll('table')
        tds = tables[1].findAll('td', {'class': 'content'})
        for td in tds:
            text = td.get_text()
            if 'Business 1' in text:
                resp.business_name = text
            elif 'Business Phone' in text:
                resp.contact_info = text
            elif 'Date Issued' in text:
                resp.issue_date = text
            elif 'Expiration' in text:
                resp.expiry_date = text
            elif 'Status' in text:
                resp.status = text           
                if 'ACTIVE' in resp.status:
                    resp.valid = True
        return resp

    def oh(self, license_num) -> Response:
        resp = StateCertifications.Response()
        # XXX no digital lookup service was provided
        resp.verifiable = False
        resp.valid = True
        return resp

    def oregon(self, license_num='162893'):
        resp = StateCertifications.Response()
        # XXX ASPX and recaptcha
        # html = requests.get(f'http://search.ccb.state.or.us/search/list_results.aspx', timeout=TIMEOUT_SECONDS)
        # soup = BeautifulSoup(html.text, 'html.parser')
        
        # event_validation = soup.find(id='__EVENTVALIDATION')
        # viewstate = soup.find(id='__VIEWSTATE')
        # viewstate_generator = soup.find(id='__VIEWSTATEGENERATOR')
        # r = requests.post('http://webcache.googleusercontent.com/search?q=cache:search.ccb.state.or.us/search/default.aspx', data={
        #     '__EVENTTARGET': '',
        #     '__EVENTARGUMENT': '',
        #     '__VIEWSTATE': viewstate.get('value'),
        #     '__VIEWSTATEGENERATOR': viewstate_generator.get('value'),
        #     '__EVENTVALIDATION': event_validation.get('value'),
        #     'ctl00$MainContent$activeToggle': "All",
        #     'ctl00$MainContent$searchBox': "162893",
        #     'ctl00$MainContent$submitbtn': "Search"
        # }, headers={'referer':'https://www.google.com/'})
        # print({
        #     '__EVENTTARGET': '',
        #     '__EVENTARGUMENT': '',
        #     '__VIEWSTATE': viewstate.get('value'),
        #     '__VIEWSTATEGENERATOR': viewstate_generator.get('value'),
        #     '__EVENTVALIDATION': event_validation.get('value'),
        #     'ctl00$MainContent$searchBox': "162893",
        # })
        # print(r.status_code)
        # print(r.content)
        resp.manual_link = 'http://search.ccb.state.or.us/search/list_results.aspx'
        resp.verifiable = False
        return resp

    def pa(self, license_num='') -> Response:
        """Does not offer licensing on a state level"""
        # TODO
        # https://www.servicetitan.com/licensing/electrician/pennsylvania
        pass

    def tx(self, license_num='20500') -> Response:
        resp = StateCertifications.Response()
        html = requests.get(f'https://www.tdlr.texas.gov/LicenseSearch/SearchResultDetail.asp?1=EECELE000{license_num}', timeout=TIMEOUT_SECONDS)
        soup = BeautifulSoup(html.text, 'html.parser')

        form  = soup.find(id='frmSearchResult')
        tr = form.findAll('tr')[-1]
        tds = tr.findAll('td')

        resp.business_name = tds[0].get_text()
        license_info = str(tds[-1])
        for info in license_info.split('<br/>'):
            if 'Expiration Date' in info:
                resp.expiry_date = info
            elif 'License Status' in info:
                resp.status = info
                if 'Active' in resp.status:
                    resp.valid = True
        return resp

    def ut(self, license_num='117206-5504') -> Response:
        resp = StateCertifications.Response()
        # XXX re-captcha
        resp.manual_link = 'https://secure.utah.gov/llv/search/index.html'
        resp.verifiable = False
        return

    def va(self, license_num='2705001045') -> Response:
        resp = StateCertifications.Response()
        html = requests.post(
            f'https://dporweb.dpor.virginia.gov/LicenseLookup/AdvancedSearch',
            data={
                'phone-number': "",
                'search-number': license_num,
                'search-name': "",
                'search-location': ""
            },
            timeout=TIMEOUT_SECONDS)
        soup = BeautifulSoup(html.text, 'html.parser')

        details = soup.find(id='license-details-tab')
        cells = details.find_all("div", class_="col-xs-6")
        data = {}
        last_key = ''
        for idx, c in enumerate(cells):
            if idx % 2 == 0:  # even idx
                last_key = c.find('strong').get_text()
                data[last_key] = ''
                continue
            data[last_key] = c.get_text()
        
        resp.business_name = data.get('name')
        resp.issue_date = data.get('Initial Certification Date')
        resp.expiry_date = data.get('Expiration Date')
        resp.status = data.get('Status')
        expiry_dt = datetime.strptime(resp.expiry_date, '%Y-%m-%d')
        if expiry_dt > datetime.now():
            resp.valid = True
        return resp

    def wa(self, license_num='BRENNBL972CC') -> Response:
        resp = StateCertifications.Response()
        # TODO try selenium layers
        # https://github.com/yai333/Selenium-UI-testing-with-AWS-Lambda-Layers

        # html = requests.get(f'https://secure.lni.wa.gov/verify/Detail.aspx?LIC={license_num}')
        # soup = BeautifulSoup(html.text, 'html.parser')

        # resp.business_name = soup.find(id='BusinessName').get_text()
        # resp.contact_info = soup.find(id='persInfoContainer').get_text()
        # resp.issue_date = soup.find(id='EffectiveDate').get_text()
        # resp.expiry_date = soup.find(id='StatusDescription').get_text()
        # resp.status = soup.find(id='StatusDescription').get_text()
        # if 'Active' in resp.status:
        #     resp.valid = True
        resp.manual_link = 'https://secure.lni.wa.gov/verify/'
        resp.verifiable = False
        return resp
        