import unittest
import os
import tempfile
import shutil
from bots import ChatGPT_Bot
from bots.foundation.base import Engines
from bots.tools.code_tools import view
from bots import ChatGPT_Bot
from bots.foundation.base import Engines
from bots.tools.code_tools import view

class TestGPTBot(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory
        self.temp_dir = tempfile.mkdtemp()
        self.bot = ChatGPT_Bot(model_engine=Engines.GPT4TURBO, max_tokens=1000, temperature=0.7, name='TestBot')
        self.bot.add_tools(view)

        # Create a test file in the temporary directory
        self.test_file_path = os.path.join(self.temp_dir, 'test_file.txt')
        self.test_content = 'This is a test file content.'
        with open(self.test_file_path, 'w') as f:
            f.write(self.test_content)

    def tearDown(self):
        # Clean up the temporary directory and all its contents
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_gptbot_read_file(self):
        response1 = self.bot.respond(f"Please display the contents of the file {self.test_file_path}")
        print(response1)    
        self.bot.save(os.path.join(self.temp_dir, "gpttestresult.bot"))
        self.assertIn(self.test_content, response1)

import sys
import traceback
def debug_on_error(type, value, tb):
    traceback.print_exception(type, value, tb)
    print("\n--- Entering post-mortem debugging ---")
    import pdb
    pdb.post_mortem(tb)

def main():
    t = TestGPTBot()
    t.setUp()
    t.test_gptbot_read_file()
    t.tearDown()

if __name__ == '__main__':
    unittest.main()
    # sys.excepthook = debug_on_error
    # main()
