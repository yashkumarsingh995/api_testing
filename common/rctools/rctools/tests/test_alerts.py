from rctools.alerts.customer import create_customer_new_job_alert


def test__create_customer_new_job_alert():
    alert = create_customer_new_job_alert('foo', 'Test Content')
    assert alert.uid == 'foo'
    assert alert.content == 'Test Content'
