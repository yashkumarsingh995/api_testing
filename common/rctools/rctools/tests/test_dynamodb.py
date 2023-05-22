from rctools.aws.dynamodb import DynamoPrimaryKey


def test__only_partition_key():
    pk = DynamoPrimaryKey()
    pk.partition = {'foo': 'bar'}
    assert len(pk.keys()) == 1


def test__only_sort_key():
    pk = DynamoPrimaryKey()
    pk.sort = {'foo': 1}
    assert len(pk.keys()) == 1


def test__sort_is_int():
    pk = DynamoPrimaryKey()
    pk.sort = {'foo': 1}
    assert pk.sort.get_typed_value() == 1
