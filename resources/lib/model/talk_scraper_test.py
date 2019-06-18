import timeit
import unittest

import mock
import requests

import talk_scraper
from test_util import skip_ted_rate_limited, CachedHTMLProvider, EXCLUDE_RATE_LIMITED


class TestTalkScraper(unittest.TestCase):

    def test_get_ted_video(self):
        self.assert_talk_details("http://www.ted.com/talks/ariel_garten_know_thyself_with_a_brain_scanner.html", "/ArielGarten_2011X-180k.mp4", "Know thyself, with a brain scanner", "Ariel Garten", True, True)

    @skip_ted_rate_limited
    def test_get_ted_video_more(self):
        # More examples?
        self.assert_talk_details("http://www.ted.com/talks/tom_shannon_s_magnetic_sculpture.html", "/TomShannon_2003-180k.mp4", "Anti-gravity sculpture", "Tom Shannon", True, True);

        # youtube link - not supported
        self.assert_talk_details("http://www.ted.com/talks/seth_godin_this_is_broken_1.html", "plugin://plugin.video.youtube/?action=play_video&videoid=aNDiHSHYI_c", "This is broken", "Seth Godin", False, True)

    def assert_talk_details(self, talk_url, expected_video_url, expected_title, expected_speaker, expect_plot, expect_json):
        logger = mock.MagicMock()
        video_url, title, speaker, plot, talk_json = talk_scraper.get(CachedHTMLProvider().get_HTML(talk_url), logger)
        self.assertTrue(video_url.endswith(expected_video_url), msg=video_url)
        self.assertEqual(expected_title, title)
        self.assertEqual(expected_speaker, speaker)

        if expect_plot:
            self.assertTrue(plot)  # Not None or empty
        else:
            self.assertIsNone(plot)

        if expect_json:
            self.assertTrue(talk_json)  # Not None or empty
        else:
            self.assertIsNone(talk_json)

    def test_get_custom_quality_video_pre_2017(self):
        html = CachedHTMLProvider().get_HTML("http://www.ted.com/talks/edith_widder_how_we_found_the_giant_squid.html")

        self.assert_custom_quality_url(html, "64kbps", "/EdithWidder_2013-64k.mp4")
        self.assert_custom_quality_url(html, "180kbps", "/EdithWidder_2013-180k.mp4")
        self.assert_custom_quality_url(html, "320kbps", "/EdithWidder_2013-320k.mp4")
        self.assert_custom_quality_url(html, "450kbps", "/EdithWidder_2013-450k.mp4")
        self.assert_custom_quality_url(html, "600kbps", "/EdithWidder_2013-600k.mp4")
        self.assert_custom_quality_url(html, "950kbps", "/EdithWidder_2013-950k.mp4")
        self.assert_custom_quality_url(html, "1500kbps", "/EdithWidder_2013-1500k.mp4")

        # Fall back to standard URL when custom URL 404s
        self.assert_custom_quality_url(html, "42kbps", "/EdithWidder_2013-180k.mp4")

    def test_get_custom_quality_video_2017(self):
        html = CachedHTMLProvider().get_HTML("https://www.ted.com/talks/dan_bricklin_meet_the_inventor_of_the_electronic_spreadsheet")

        self.assert_custom_quality_url(html, "1500kbps", "/DanBricklin_2016X-1500k.mp4")

        # Fall back to standard URL when custom URL 404s
        self.assert_custom_quality_url(html, "42kbps", "/DanBricklin_2016X-180k.mp4")

    def assert_custom_quality_url(self, talk_html, video_quality, expected_video_url):
        logger = mock.MagicMock()
        video_url, title, speaker, plot, talk_json = talk_scraper.get(talk_html, logger, video_quality)
        if not EXCLUDE_RATE_LIMITED:
            self.assertEqual(200, requests.head(video_url, allow_redirects=True).status_code)
        self.assertTrue(video_url.endswith(expected_video_url), msg=video_url)

    @skip_ted_rate_limited
    def test_performance(self):
        html = CachedHTMLProvider().get_HTML("http://www.ted.com/talks/ariel_garten_know_thyself_with_a_brain_scanner.html")
        logger = mock.MagicMock()

        def test():
            talk_scraper.get(html, logger)

        t = timeit.Timer(test)
        repeats = 10
        time = t.timeit(repeats)
        print("Extracting talk details took %s seconds per run" % (time / repeats))
        self.assertGreater(4, time)

