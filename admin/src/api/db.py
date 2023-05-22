dashboardData = {  # XXX
    'cards': [
        {
            'id': 1,
            'statName': 'Installers',
            'link': 'See All Installers',
            'path': '/installers',
            'entries': [
                    {
                        'lineName': 'Total',
                        'number': '312'
                    },
                {
                        'lineName': 'Available',
                        'number': '205'
                    }
            ]
        },
        {
            'id': 2,
            'statName': 'Customers',
            'link': 'See All Customers',
            'path': '/customers',
            'entries': [
                    {
                        'lineName': 'Total',
                        'number': '312'
                    },
                {
                        'lineName': 'Scheduled',
                        'number': '205'
                    }
            ]
        },
        {
            'id': 3,
            'statName': 'Jobs',
            'link': 'See All Jobs',
            'path': '/job-tickets',
            'entries': [
                    {
                        'lineName': 'Total',
                        'number': '312'
                    },
                {
                        'lineName': 'Scheduled',
                        'number': '205'
                    },
                {
                        'lineName': 'Available',
                        'number': '1'
                    }
            ]
        },
        {
            'id': 4,
            'statName': 'Support Tickets',
            'link': 'See All Installers',
            'path': '/installers',
            'entries': [
                    {
                        'lineName': 'Total',
                        'number': '312'
                    },
                {
                        'lineName': 'Day Total',
                        'number': '205'
                    },
                {
                        'lineName': 'Opened',
                        'number': '1'
                    },
                {
                        'lineName': 'Resolved',
                        'number': '1'
                    },
                {
                        'lineName': 'High Severity',
                        'number': '1'
                    }
            ]
        },
        {
            'id': 5,
            'statName': 'Chargers',
            'link': 'See All Installers',
            'path': '/installers',
            'entries': [
                    {
                        'lineName': 'Total',
                        'number': '312'
                    },
                {
                        'lineName': 'Scheduled',
                        'number': '205'
                    },
                {
                        'lineName': 'Available',
                        'number': '1'
                    }
            ]
        }
    ],
    'messages': [],
    'tickets': [],
    'reports': []
}

installerData = [
    {
        "id": "1",
        "name": "John Smith",
        "type": "Company",
        "jobs": 16,
        "state": "MI",
        "rating": 3,
        "email": "name@email.com",
        "phone": "(000) 000-0000",
        "address1": "123 Main St",
        "address2": "Sutie #200",
        "city": "ann arbor",
        "companyName": "John Smith",
        "region": 48105,
        "preferred": True,
        "referred": False,
        "companyInstallers": [
                {
                    "id": "1",
                    "experience": 3,
                    "name": "Georgs at Company",
                    "type": "Company",
                    "jobs": 16,
                    "state": "MI",
                    "rating": 3,
                    "email": "name@email.com",
                    "phone": "(000) 000-0000",
                    "address1": "123 Main St",
                    "address2": "Sutie #200",
                    "city": "ann arbor",
                    "companyName": "Company Inc.",
                    "region": 48105
                },
            {
                    "id": "2",
                    "experience": 4,
                    "name": "Jane at Company",
                    "type": "Individual",
                    "jobs": 30,
                    "state": "MI",
                    "rating": 4,
                    "email": "name@email.com",
                    "phone": "(000) 000-0000",
                    "address1": "123 Main St",
                    "address2": "Sutie #200",
                    "city": "ann arbor",
                    "companyName": "Company Inc.",
                    "region": 48105
            },
            {
                    "id": "3",
                    "experience": 2,
                    "name": "John At company",
                    "type": "Company",
                    "jobs": 1,
                    "state": "AR",
                    "rating": 1,
                    "email": "name@email.com",
                    "phone": "(000) 000-0000",
                    "address1": "123 Main St",
                    "address2": "Sutie #200",
                    "city": "ann arbor",
                    "companyName": "Company Inc.",
                    "region": 48105
            }
        ],
        "account": {
            "email": "name@email.com",
            "phone": "(000) 000-0000",
            "address1": "123 Main St",
            "address2": "Sutie #200",
            "city": "ann arbor",
            "companyName": "Company Inc. Owner",
            "state": "MI",
            "region": 48105
        }
    },
    {
        "id": "2",
        "name": "Jane Smith",
        "type": "Individual",
        "jobs": 30,
        "state": "MI",
        "rating": 4,
        "email": "name@email.com",
        "phone": "(000) 000-0000",
        "address1": "123 Main St",
        "address2": "Sutie #200",
        "city": "ann arbor",
        "companyName": "Jane Smith",
        "region": 48105,
        "preferred": False,
        "referred": True,
        "companyInstallers": [
                {
                    "id": "1",
                    "experience": 3,
                    "name": "Georgs at Company",
                    "type": "Company",
                    "jobs": 16,
                    "state": "MI",
                    "rating": 3,
                    "email": "name@email.com",
                    "phone": "(000) 000-0000",
                    "address1": "123 Main St",
                    "address2": "Sutie #200",
                    "city": "ann arbor",
                    "companyName": "Company Inc.",
                    "region": 48105
                },
            {
                    "id": "2",
                    "experience": 4,
                    "name": "Jane at Company",
                    "type": "Individual",
                    "jobs": 30,
                    "state": "MI",
                    "rating": 4,
                    "email": "name@email.com",
                    "phone": "(000) 000-0000",
                    "address1": "123 Main St",
                    "address2": "Sutie #200",
                    "city": "ann arbor",
                    "companyName": "Company Inc.",
                    "region": 48105
            },
            {
                    "id": "3",
                    "experience": 2,
                    "name": "John At company",
                    "type": "Company",
                    "jobs": 1,
                    "state": "AR",
                    "rating": 1,
                    "email": "name@email.com",
                    "phone": "(000) 000-0000",
                    "address1": "123 Main St",
                    "address2": "Sutie #200",
                    "city": "ann arbor",
                    "companyName": "Company Inc.",
                    "region": 48105
            }
        ],
        "account": {
            "email": "name@email.com",
            "phone": "(000) 000-0000",
            "address1": "123 Main St",
            "address2": "Sutie #200",
            "city": "ann arbor",
            "companyName": "Company Inc.",
            "state": "MI",
            "region": 48105
        }
    },
    {
        "id": "3",
        "name": "Tesla Installers",
        "type": "Individual",
        "jobs": 12,
        "state": "MI",
        "rating": 4,
        "email": "name@email.com",
        "phone": "(000) 000-0000",
        "address1": "123 Main St",
        "address2": "Sutie #200",
        "city": "ann arbor",
        "companyName": "Tesla Installers",
        "region": 48105,
        "preferred": False,
        "referred": False,
        "companyInstallers": [
                {
                    "id": "1",
                    "experience": 3,
                    "name": "Georgs at Company",
                    "type": "Company",
                    "jobs": 16,
                    "state": "MI",
                    "rating": 3,
                    "email": "name@email.com",
                    "phone": "(000) 000-0000",
                    "address1": "123 Main St",
                    "address2": "Sutie #200",
                    "city": "ann arbor",
                    "companyName": "Company Inc.",
                    "region": 48105
                },
            {
                    "id": "2",
                    "experience": 4,
                    "name": "Jane at Company",
                    "type": "Individual",
                    "jobs": 30,
                    "state": "MI",
                    "rating": 4,
                    "email": "name@email.com",
                    "phone": "(000) 000-0000",
                    "address1": "123 Main St",
                    "address2": "Sutie #200",
                    "city": "ann arbor",
                    "companyName": "Company Inc.",
                    "region": 48105
            },
            {
                    "id": "3",
                    "experience": 2,
                    "name": "John At company",
                    "type": "Company",
                    "jobs": 1,
                    "state": "AR",
                    "rating": 1,
                    "email": "name@email.com",
                    "phone": "(000) 000-0000",
                    "address1": "123 Main St",
                    "address2": "Sutie #200",
                    "city": "ann arbor",
                    "companyName": "Company Inc.",
                    "region": 48105
            }
        ],
        "account": {
            "email": "name@email.com",
            "phone": "(000) 000-0000",
            "address1": "123 Main St",
            "address2": "Sutie #200",
            "city": "ann arbor",
            "companyName": "Company Inc.",
            "state": "MI",
            "region": 48105
        }
    },
    {
        "id": "4",
        "name": "Company Inc.",
        "type": "Company",
        "jobs": 51,
        "state": "AR",
        "rating": 5,
        "email": "name@email.com",
        "phone": "(000) 000-0000",
        "address1": "123 Main St",
        "address2": "Sutie #200",
        "city": "ann arbor",
        "companyName": "Company Inc.",
        "region": 48105,
        "preferred": False,
        "referred": False,
        "companyInstallers": [
                {
                    "id": "1",
                    "experience": 3,
                    "name": "Georgs at Company",
                    "type": "Company",
                    "jobs": 16,
                    "state": "MI",
                    "rating": 3,
                    "email": "name@email.com",
                    "phone": "(000) 000-0000",
                    "address1": "123 Main St",
                    "address2": "Sutie #200",
                    "city": "ann arbor",
                    "companyName": "Company Inc.",
                    "region": 48105
                },
            {
                    "id": "2",
                    "experience": 4,
                    "name": "Jane at Company",
                    "type": "Individual",
                    "jobs": 30,
                    "state": "MI",
                    "rating": 4,
                    "email": "name@email.com",
                    "phone": "(000) 000-0000",
                    "address1": "123 Main St",
                    "address2": "Sutie #200",
                    "city": "ann arbor",
                    "companyName": "Company Inc.",
                    "region": 48105
            },
            {
                    "id": "3",
                    "experience": 2,
                    "name": "John At company",
                    "type": "Company",
                    "jobs": 1,
                    "state": "AR",
                    "rating": 1,
                    "email": "name@email.com",
                    "phone": "(000) 000-0000",
                    "address1": "123 Main St",
                    "address2": "Sutie #200",
                    "city": "ann arbor",
                    "companyName": "Company Inc.",
                    "region": 48105
            }
        ],
        "account": {
            "email": "name@email.com",
            "phone": "(000) 000-0000",
            "address1": "123 Main St",
            "address2": "Sutie #200",
            "city": "ann arbor",
            "companyName": "Company Inc.",
            "state": "AR",
            "region": 48105
        }
    }
]

customersData = [
    {
        "id": "1",
        "name": "John Smith",
        "type": "Company",
        "state": "MI",
        "region": 48105
    },
    {
        "id": "2",
        "name": "Jane Smith",
        "type": "Individual",
        "state": "MI",
        "region": 48105
    },
    {
        "id": "3",
        "name": "John Doe",
        "type": "Company",
        "state": "AR",
        "region": 48105
    }
]

jobTicketsData = [
  {
    "id": "1",
    "job_number": "18",
    "date": "2022-10-06",
    "time_start": "12:00pm",
    "time_end": "1:30pm",
    "installer": {
        "created_at": 1660968160254,
        "updated_at": 1660968160254,
        "sub": "06d5e5a0-8ad4-4fdc-9886-b703bf17078e",
        "given_name": None,
        "family_name": None,
        "name": "Thor Thorson",
        "email": "thor@thenewfoundry.com",
        "phone_number": "+17345555555",
        "scheduling": None,
        "UserCreateDate": "2022-08-20T04:02:41.544000+00:00",
        "Username": "06d5e5a0-8ad4-4fdc-9886-b703bf17078e",
        "state": "MI",
        "UserLastModifiedDate": "2022-08-20T04:02:41.687000+00:00",
        "zip": "49341",
        "addressOne": "123 Street",
        "city": "Town",
        "Enabled": True,
        "bio": {
            "yearsOfExperience": "2",
            "bio": "5"
        },
        "UserStatus": "CONFIRMED",
        "id": "06d5e5a0-8ad4-4fdc-9886-b703bf17078e"
    },
    "customer": {
        "created_at": 1660968160254,
        "updated_at": 1660968160254,
        "sub": "06d5e5a0-8ad4-4fdc-9886-b703bf17078e",
        "given_name": None,
        "family_name": None,
        "name": "Jane Customer",
        "email": "jane@fake.email",
        "phone_number": "+17345555555",
        "UserCreateDate": "2022-08-20T04:02:41.544000+00:00",
        "Username": "06d5e5a0-8ad4-4fdc-9886-b703bf17078e",
        "state": "MI",
        "UserLastModifiedDate": "2022-08-20T04:02:41.687000+00:00",
        "zip": "49341",
        "addressOne": "123 Street",
        "city": "Town",
        "Enabled": True,
        "UserStatus": "CONFIRMED",
        "id": "06d5e5a0-8ad4-4fdc-9886-b703bf17078e"
    },
    "address": "123 Main St",
    "region": "48105"
  },
  {
    "id": "2",
    "job_number": "4",
    "date": "2022-10-10",
    "time_start": "9:00am",
    "time_end": "11:30am",
    "installer": {
        "created_at": 1660968160254,
        "updated_at": 1660968160254,
        "sub": "06d5e5a0-8ad4-4fdc-9886-b703bf17078e",
        "given_name": None,
        "family_name": None,
        "name": "Thor Thorson",
        "email": "thor@thenewfoundry.com",
        "phone_number": "+17345555555",
        "scheduling": None,
        "UserCreateDate": "2022-08-20T04:02:41.544000+00:00",
        "Username": "06d5e5a0-8ad4-4fdc-9886-b703bf17078e",
        "state": "MI",
        "UserLastModifiedDate": "2022-08-20T04:02:41.687000+00:00",
        "zip": "49341",
        "addressOne": "123 Street",
        "city": "Town",
        "Enabled": True,
        "bio": {
            "yearsOfExperience": "2",
            "bio": "5"
        },
        "UserStatus": "CONFIRMED",
        "id": "06d5e5a0-8ad4-4fdc-9886-b703bf17078e"
    },
    "customer": {
        "created_at": 1660968160254,
        "updated_at": 1660968160254,
        "sub": "06d5e5a0-8ad4-4fdc-9886-b703bf17078e",
        "given_name": None,
        "family_name": None,
        "name": "Jane Customer",
        "email": "jane@fake.email",
        "phone_number": "+17345555555",
        "UserCreateDate": "2022-08-20T04:02:41.544000+00:00",
        "Username": "06d5e5a0-8ad4-4fdc-9886-b703bf17078e",
        "state": "MI",
        "UserLastModifiedDate": "2022-08-20T04:02:41.687000+00:00",
        "zip": "49341",
        "addressOne": "123 Street",
        "city": "Town",
        "Enabled": True,
        "UserStatus": "CONFIRMED",
        "id": "06d5e5a0-8ad4-4fdc-9886-b703bf17078e"
    },
    "address": "123 Main St",
    "region": "48105"
  },
  {
    "id": "3",
    "job_number": "12",
    "date": "2022-10-26",
    "time_start": "1:00pm",
    "time_end": "2:30pm",
    "installer": {
        "created_at": 1660968160254,
        "updated_at": 1660968160254,
        "sub": "06d5e5a0-8ad4-4fdc-9886-b703bf17078e",
        "given_name": None,
        "family_name": None,
        "name": "Thor Thorson",
        "email": "thor@thenewfoundry.com",
        "phone_number": "+17345555555",
        "scheduling": None,
        "UserCreateDate": "2022-08-20T04:02:41.544000+00:00",
        "Username": "06d5e5a0-8ad4-4fdc-9886-b703bf17078e",
        "state": "MI",
        "UserLastModifiedDate": "2022-08-20T04:02:41.687000+00:00",
        "zip": "49341",
        "addressOne": "123 Street",
        "city": "Town",
        "Enabled": True,
        "bio": {
            "yearsOfExperience": "2",
            "bio": "5"
        },
        "UserStatus": "CONFIRMED",
        "id": "06d5e5a0-8ad4-4fdc-9886-b703bf17078e"
    },
    "customer": {
        "created_at": 1660968160254,
        "updated_at": 1660968160254,
        "sub": "06d5e5a0-8ad4-4fdc-9886-b703bf17078e",
        "given_name": None,
        "family_name": None,
        "name": "Jane Customer",
        "email": "jane@fake.email",
        "phone_number": "+17345555555",
        "UserCreateDate": "2022-08-20T04:02:41.544000+00:00",
        "Username": "06d5e5a0-8ad4-4fdc-9886-b703bf17078e",
        "state": "MI",
        "UserLastModifiedDate": "2022-08-20T04:02:41.687000+00:00",
        "zip": "49341",
        "addressOne": "123 Street",
        "city": "Town",
        "Enabled": True,
        "UserStatus": "CONFIRMED",
        "id": "06d5e5a0-8ad4-4fdc-9886-b703bf17078e"
    },
    "address": "123 S Main",
    "region": "48105"
  },
]

reportsData = [
    {
        "id": 1,
        "type": "User",
        "date": "2/23/2022",
        "time": "12:00pm",
        "user": "John Doe"
    },
    {
        "id": 2,
        "type": "Payments",
        "date": "3/23/2022",
        "time": "1:00pm",
        "user": "Jane Doe"
    },
    {
        "id": 3,
        "type": "Analytics",
        "date": "3/23/2022",
        "time": "2:00pm",
        "user": "Walter Doe"
    },
    {
        "id": 4,
        "type": "User",
        "date": "3/23/2022",
        "time": "12:00pm",
        "user": "gabe Doe"
    },
    {
        "id": 5,
        "type": "User",
        "date": "3/23/2022",
        "time": "12:00pm",
        "user": "gene Doe"
    },
    {
        "id": 6,
        "type": "User",
        "date": "3/23/2022",
        "time": "12:00pm",
        "user": "George don"
    },
    {
        "id": 7,
        "type": "Payments",
        "date": "3/23/2022",
        "time": "12:00pm",
        "user": "George doert"
    },
    {
        "id": 8,
        "type": "User",
        "date": "3/23/2022",
        "time": "12:00pm",
        "user": "George Doc"
    },
    {
        "id": 9,
        "type": "Referrals",
        "date": "3/23/2022",
        "time": "12:00pm",
        "user": "George Doe"
    },
    {
        "id": 10,
        "type": "User",
        "date": "3/23/2022",
        "time": "1:00pm",
        "user": "George Doe"
    },
    {
        "id": 11,
        "type": "Referrals",
        "date": "3/23/2022",
        "time": "12:00am",
        "user": "George Doe"
    },
    {
        "id": 12,
        "type": "User",
        "date": "3/23/2022",
        "time": "12:01pm",
        "user": "George Doe"
    },
    {
        "id": 13,
        "type": "User",
        "date": "3/23/2022",
        "time": "8:00pm",
        "user": "George Doe"
    },
    {
        "id": 14,
        "type": "Analytics",
        "date": "3/23/2022",
        "time": "12:00pm",
        "user": "George Doe"
    },
    {
        "id": 15,
        "type": "User",
        "date": "3/23/2022",
        "time": "12:00pm",
        "user": "George Doe"
    },
    {
        "id": 16,
        "type": "User",
        "date": "3/23/2022",
        "time": "12:01am",
        "user": "George Doe"
    },
    {
        "id": 17,
        "type": "User",
        "date": "3/23/2022",
        "time": "9:00am",
        "user": "Jane Dot"
    },
    {
        "id": 18,
        "type": "Payments",
        "date": "3/23/2022",
        "time": "12:02pm",
        "user": "George Doe"
    },
    {
        "id": 19,
        "type": "Payments",
        "date": "3/23/2022",
        "time": "12:02pm",
        "user": "George Doe"

    },
    {
        "id": 20,
        "type": "Payments",
        "date": "3/23/2022",
        "time": "12:02pm",
        "user": "Jack Doe"

    },
    {
        "id": 21,
        "type": "Analytics",
        "date": "3/23/2022",
        "time": "12:02pm",
        "user": "Jill Doe"
    }
]
