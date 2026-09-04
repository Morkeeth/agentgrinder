import pytest
from agentgrinder.rig_config import preview,select,current,validate


def test_preview_import_and_revert(tmp_path):
    first={'schema_version':1,'manifest':{'model':'first','skills':['check']}}
    second={'schema_version':1,'manifest':{'model':'second','skills':['check']}}
    assert preview(first,tmp_path)
    assert current(tmp_path) is None
    saved=select(first,tmp_path)
    assert preview(second,tmp_path)==[{'field':'model','before':'first','after':'second'}]
    select(second,tmp_path)
    select(saved['document'],tmp_path)
    assert current(tmp_path)['revision']==saved['revision']
    assert len(list(tmp_path.glob('*.json')))==3


def test_executable_or_private_configuration_is_rejected():
    for manifest in [{'command':'curl somewhere'},{'notes':'/Users/fixture/private'},{'mcps':[{'token':'x'}]}]:
        with pytest.raises(ValueError):validate({'schema_version':1,'manifest':manifest})
