import os
import unittest
from unittest.mock import Mock

import mr_state

MERGE_REQUEST_TEST_DATA = os.path.join(os.path.dirname(__file__), 'test_data/merge-requests.test.json')
TEST_CONFIG = os.path.join(os.path.dirname(__file__), 'test_data/test-config.ini')


class TestAdd(unittest.TestCase):
    """
    Test mr_state
    """

    def setUp(self):
        self.config = mr_state.Config(TEST_CONFIG)
        self.original_get_password = mr_state.get_password
        mr_state.get_password = lambda service_name, username: "aaabbb"

    def tearDown(self):
        mr_state.get_password = self.original_get_password
        self.config = None

    def test_config(self):
        self.assertEqual(self.config.group_id, 44)
        self.assertEqual(self.config.group_name, "mygroup")
        self.assertEqual(self.config.base_url, "https://gitlab.com")
        self.assertEqual(self.config.user_id, 13)
        self.assertEqual(self.config.web_browser, "chromium")
        self.assertEqual(self.config.label, "GitLab:")
        self.assertEqual(self.config.approved_merge_requests_label, "Approved Gitlab MRs:")
        self.assertEqual(self.config.all_merge_requests_label, "All MRs:")

    def test_get_open_merge_requests_url(self):
        url = mr_state.get_open_merge_requests_url(self.config)
        self.assertEqual(url, "https://gitlab.com/api/v4/groups/44/merge_requests?state=opened")

    def test_get_token(self):
        self.assertEqual(mr_state.get_token(), "aaabbb")

    def test_create_request(self):
        request = mr_state.create_request("http://example.com", "aaabbb")
        self.assertEqual(request.get_header("Private-token"), "aaabbb")

    def test_get_response_and_filter_open_merge_requests(self):
        def mocked_urlopen(request):
            test_data = open(MERGE_REQUEST_TEST_DATA)
            test_data_read = test_data.read()
            test_data.close()
            attrs = {'read.return_value': bytes(test_data_read, "utf-8")}
            mock = Mock()
            mock.configure_mock(**attrs)
            return mock

        original_urlopen = mr_state.urlopen
        mr_state.urlopen = mocked_urlopen

        open_merge_requests = mr_state.get_response({})
        self.assertEqual(open_merge_requests[0]["id"], 4159)
        self.assertEqual(open_merge_requests[2]["title"], "WIP: Some fixes")
        open_merge_requests_without_wip = mr_state.get_open_merge_requests_without_wip(open_merge_requests)
        self.assertNotEqual(open_merge_requests_without_wip[2]["title"], "WIP: Some fixes")

        mr_state.urlopen = original_urlopen

    def test_get_approvals_url(self):
        url = mr_state.get_approvals_url(self.config.base_url, mr_state.MergeRequestIds(5, 555))
        self.assertEqual(url, "https://gitlab.com/api/v4/projects/5/merge_requests/555/approvals")

    def test_get_approvals(self):
        def mocked_urlopen(request):
            test_data = open(MERGE_REQUEST_TEST_DATA)
            test_data_read = test_data.read()
            test_data.close()
            attrs = {'read.return_value': bytes(test_data_read, "utf-8")}
            mock = Mock()
            mock.configure_mock(**attrs)
            return mock

        original_urlopen = mr_state.urlopen
        mr_state.urlopen = mocked_urlopen

        open_merge_requests = mr_state.get_response({})
        self.assertEqual(open_merge_requests[0]["id"], 4159)
        self.assertEqual(open_merge_requests[2]["title"], "WIP: Some fixes")
        open_merge_requests_without_wip = mr_state.get_open_merge_requests_without_wip(open_merge_requests)
        self.assertNotEqual(open_merge_requests_without_wip[2]["title"], "WIP: Some fixes")

        mr_state.urlopen = original_urlopen


if __name__ == '__main__':
    unittest.main()
