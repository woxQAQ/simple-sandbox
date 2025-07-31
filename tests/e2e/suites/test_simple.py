"""
简单测试文件
"""


def test_simple():
    """简单测试"""
    assert 1 + 1 == 2


class TestSimpleClass:
    """简单测试类"""

    def test_method(self):
        """测试方法"""
        assert "hello" == "hello"
