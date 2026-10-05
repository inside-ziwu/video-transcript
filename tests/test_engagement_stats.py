"""视频号互动数:解析、字段语义与 VT_OUTPUTS 放行规则。

互动数语义:favCount=点赞、likeCount=推荐、
forwardCount=转发、commentCount=评论。视频号没有收藏数。
"""

import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

import sph_resolver  # noqa: E402
import transcript  # noqa: E402


class ParseCountTests(unittest.TestCase):
    def test_plain_digits(self):
        self.assertEqual(sph_resolver.parse_count("2081"), 2081)
        self.assertEqual(sph_resolver.parse_count("0"), 0)

    def test_integers_pass_through(self):
        self.assertEqual(sph_resolver.parse_count(316), 316)

    def test_chinese_units(self):
        self.assertEqual(sph_resolver.parse_count("1.2万"), 12000)
        self.assertEqual(sph_resolver.parse_count("3万"), 30000)
        self.assertEqual(sph_resolver.parse_count("1.2亿"), 120000000)

    def test_separators_and_lower_bound_marker(self):
        self.assertEqual(sph_resolver.parse_count(" 1,234 "), 1234)
        self.assertEqual(sph_resolver.parse_count("1000+"), 1000)

    def test_unreadable_values_are_none(self):
        for value in (None, "", "  ", "很多", True, [], -5):
            self.assertIsNone(sph_resolver.parse_count(value), value)

    def test_non_finite_numbers_do_not_crash_the_resolver(self):
        # float() 收 "nan"/"inf",int() 不收:认不出就给 None,不能把解析器带崩。
        for value in ("nan", "inf", "-inf", float("nan"), float("inf")):
            self.assertIsNone(sph_resolver.parse_count(value), value)


class StatCountTests(unittest.TestCase):
    def test_prefers_raw_integer_field(self):
        info = {"favCount": 316, "favCountFmt": "3.1万"}
        self.assertEqual(sph_resolver.stat_count(info, "favCount"), 316)

    def test_falls_back_to_display_string(self):
        info = {"favCountFmt": "2081"}
        self.assertEqual(sph_resolver.stat_count(info, "favCount"), 2081)

    def test_raw_zero_beats_the_display_string(self):
        # 0 是合法互动数,不能因为 falsy 就退回展示串。
        self.assertEqual(sph_resolver.stat_count({"favCount": 0, "favCountFmt": "2081"}, "favCount"), 0)

    def test_missing_field_is_none(self):
        self.assertIsNone(sph_resolver.stat_count({}, "commentCount"))

    def test_unreadable_display_string_is_none(self):
        self.assertIsNone(sph_resolver.stat_count({"favCountFmt": "很多"}, "favCount"))


class ProfileFromFeedTests(unittest.TestCase):
    def test_maps_the_four_metrics(self):
        feed = {
            "data": {
                "feedInfo": {
                    "description": "一条口播",
                    "favCountFmt": "2081",
                    "likeCountFmt": "1967",
                    "forwardCountFmt": "2255",
                    "commentCountFmt": "98",
                },
                "authorInfo": {"nickname": "博主"},
            }
        }
        stats = sph_resolver.profile_from_feed("https://weixin.qq.com/sph/x", feed)["stats"]
        self.assertEqual(
            stats,
            {"favCount": 2081, "likeCount": 1967, "forwardCount": 2255, "commentCount": 98},
        )

    def test_missing_metrics_are_explicit_null(self):
        stats = sph_resolver.profile_from_feed("https://weixin.qq.com/sph/x", {})["stats"]
        self.assertEqual(
            stats,
            {
                "favCount": None,
                "likeCount": None,
                "forwardCount": None,
                "commentCount": None,
            },
        )


class PublisherOutputFieldsTests(unittest.TestCase):
    def test_integers_pass(self):
        fields = transcript.publisher_output_fields(
            {
                "author": "博主",
                "description": "正文",
                "stats": {
                    "favCount": 316,
                    "likeCount": 20,
                    "forwardCount": 8,
                    "commentCount": 0,
                },
            }
        )
        self.assertEqual(
            fields,
            {
                "author": "博主",
                "description": "正文",
                "favCount": 316,
                "likeCount": 20,
                "forwardCount": 8,
                "commentCount": 0,
            },
        )

    def test_nulls_pass_explicitly(self):
        fields = transcript.publisher_output_fields(
            {
                "stats": {
                    "favCount": None,
                    "likeCount": None,
                    "forwardCount": None,
                    "commentCount": None,
                }
            }
        )
        self.assertEqual(
            fields,
            {
                "favCount": None,
                "likeCount": None,
                "forwardCount": None,
                "commentCount": None,
            },
        )

    def test_missing_keys_are_omitted_and_strings_become_null(self):
        fields = transcript.publisher_output_fields({"stats": {"favCount": "2081"}})
        self.assertEqual(fields, {"favCount": None})

    def test_no_stats_means_no_engagement_keys(self):
        self.assertEqual(transcript.publisher_output_fields({"author": "博主"}), {"author": "博主"})

    def test_legacy_formatted_keys_are_gone(self):
        fields = transcript.publisher_output_fields(
            {"stats": {"like": "1958", "fav": "2070", "forward": "2238", "comment": "98"}}
        )
        self.assertEqual(fields, {})


if __name__ == "__main__":
    unittest.main()
