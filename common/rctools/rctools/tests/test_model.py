from mergedeep import merge
from rctools.models import Message, ReadiChargeBaseModel, IdMixin, JobTicket, Installer, License


def test__ReadiChargeBaseModel_has_timestamps():
    m = ReadiChargeBaseModel()
    assert 'created_at' in m.dict() and 'updated_at' in m.dict()


def test__default_fn_values():
    m = Message(conversation_id=1, text='foo')
    assert m.id
    assert m.ts > 0


def test__id_mixin_doesnt_overwrite_existing():
    class TestModel(IdMixin, ReadiChargeBaseModel):
        pass

    t = TestModel()
    assert t.id
    saved_id = t.id
    t2 = TestModel(**t.dict())
    assert t.id == t2.id


def test__base_message_has_unique_id():
    m1 = Message(conversation_id=1, text='foo')
    m2 = Message(conversation_id=1, text='bar')
    assert m1.id
    assert m2.id and m2.id != m1.id


def test__creating_job_scope():
    j = JobTicket(customer_id=1)
    home = {
        'job_scope': {
            'home': {
                'year_built': 1970,
                'rent_own': 'own',
                'panel_upgraded': 'yes'
            }
        }
    }
    new_j = JobTicket(**{**j.dict(), **home})
    assert new_j.job_scope.home.year_built == 1970


def test__updating_job_scope():
    j = JobTicket(customer_id=1)
    home = {
        'job_scope': {
            'home': {
                'year_built': 1970,
                'rent_own': 'own',
                'panel_upgraded': 'yes'
            }
        }
    }
    new_j = JobTicket(**{**j.dict(), **home})
    chargers = {
        'job_scope': {
            'chargers': {
                'num_chargers': 2,
                'purchased': [{'purchased': False}, {'purchased': False}]
            }
        }
    }
    second_new_j = JobTicket(**merge(new_j.dict(), chargers))
    assert second_new_j.job_scope.home.year_built == 1970
    assert second_new_j.job_scope.chargers.num_chargers == 2


def test__user_when_data_has_None():
    i = Installer()
    data = i.dict()
    assert data['background_check'] == None
    data = i.dict(exclude_none=True)
    assert 'background_check' not in data
    assert 'licensing' not in data


def test__data_override():
    """Verify that dictionary update with exclude_none works w/o deleting existing fields"""
    i = Installer()
    i.license = License(licenseNumber='foo')
    update = Installer().dict(exclude_none=True)
    data = i.dict()
    data.update(update)
    assert data['license']['licenseNumber'] == 'foo'
