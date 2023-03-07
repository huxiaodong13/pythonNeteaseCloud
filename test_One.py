import unittest
import random
class Test_one(unittest.TestCase):
    def setUp(self) -> None:
        print('测试用例初始化')
        self.pas = False

    def tearDown(self) -> None:
        if self.pas == False:
            print("测试用例失败，清除环境")
        print("用例结束清除环境")

    def test_1(self):
        a = random.randint(4,7)
        b = 5
        self.assertEqual(a,b)
        self.pas = True


if __name__ == '__main__':
    unittest.main()
