from rctools.aws.cognito import format_phone_number, merge_user_data


def test__merge_user_data():
    user = {
        'sub': 'id',
        'foo': 'A',
        'bar': 'B',
        'Attributes': [{
            'Name': 'hello',
            'Value': 'world'
        }]
    }
    merge_user_data(user, {})
    assert user['hello'] == 'world'


def test__format_phone_number():
    a = '2345678901'
    b = '12345678901'
    c = '+12345678901'

    assert format_phone_number(a) == c
    assert format_phone_number(b) == c
    assert format_phone_number(c) == c
