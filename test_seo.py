"""Unit tests for SEO Auditor"""
import pytest
import json
from seo_audit import (
    SEOAuditor, AuditResult, TitleResult, MetaDescResult,
    HeadingsResult, SchemaResult, ImageAltResult,
    ResponsiveResult, IndexableResult, CanonicalResult,
    InternalLinksResult, OGTagsResult, SSLResult,
    CDPVitalsResult, StickyResult, HeroResult,
    BreadcrumbsResult, ContactFormResult
)

# ── Sample HTML snippets ──

SAMPLE_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <title>Test Page Title | Sample Site</title>
    <meta name="description" content="This is a test meta description for SEO testing.">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="robots" content="index, follow">
    <meta property="og:title" content="OG Test Title">
    <meta property="og:description" content="OG description test">
    <meta property="og:image" content="https://example.com/og-image.jpg">
    <meta property="og:url" content="https://example.com/page">
    <meta property="og:type" content="article">
    <meta property="og:site_name" content="Example Site">
    <link rel="canonical" href="https://example.com/page">
    <script type="application/ld+json">
    {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": "Test Page"
    }
    </script>
</head>
<body>
    <h1>Main Heading</h1>
    <p>First paragraph.</p>
    <h2>Subheading</h2>
    <p>Second paragraph.</p>
    <h2>Another Subheading</h2>
    <h3>Deep Heading</h3>
    <p>More content here.</p>
    <img src="https://example.com/image1.jpg" alt="Image 1 description">
    <img src="https://example.com/image2.jpg">
    <a href="https://example.com/page1">Internal Link 1</a>
    <a href="https://example.com/page2">Internal Link 2</a>
    <a href="https://external.com/page">External Link</a>
    <a href="#anchor">Anchor Link</a>
    <a href="javascript:void(0)">JS Link</a>
</body>
</html>"""


class TestTitleCheck:
    def test_title_extraction(self):
        r = AuditResult(url="https://example.com")
        auditor = SEOAuditor(url="https://example.com")
        auditor._check_title(SAMPLE_HTML, r)
        assert r.title.text == "Test Page Title | Sample Site"
        assert r.title.length == 29
        assert r.title.status == "GOOD"

    def test_title_too_long(self):
        r = AuditResult(url="https://example.com")
        auditor = SEOAuditor(url="https://example.com")
        html = '<html><head><title>' + 'A' * 65 + '</title></head><body></body></html>'
        auditor._check_title(html, r)
        assert r.title.status == "TOO LONG"
        assert r.title.passed is False

    def test_title_warning(self):
        r = AuditResult(url="https://example.com")
        auditor = SEOAuditor(url="https://example.com")
        html = '<html><head><title>' + 'A' * 55 + '</title></head><body></body></html>'
        auditor._check_title(html, r)
        assert r.title.status == "WARNING"

    def test_title_missing(self):
        r = AuditResult(url="https://example.com")
        auditor = SEOAuditor(url="https://example.com")
        auditor._check_title("<html><head></head><body></body></html>", r)
        assert r.title.status == "MISSING"
        assert r.title.passed is False


class TestMetaDescription:
    def test_meta_extraction(self):
        r = AuditResult(url="https://example.com")
        auditor = SEOAuditor(url="https://example.com")
        auditor._check_meta_desc(SAMPLE_HTML, r)
        assert r.meta_desc.length == 48
        assert r.meta_desc.status == "GOOD"

    def test_meta_too_long(self):
        r = AuditResult(url="https://example.com")
        auditor = SEOAuditor(url="https://example.com")
        html = '<html><head><meta name="description" content="' + 'A' * 165 + '"></head></html>'
        auditor._check_meta_desc(html, r)
        assert r.meta_desc.status == "TOO LONG"

    def test_meta_missing(self):
        r = AuditResult(url="https://example.com")
        auditor = SEOAuditor(url="https://example.com")
        auditor._check_meta_desc("<html><head></head></html>", r)
        assert r.meta_desc.status == "MISSING"


class TestHeadingsCheck:
    def test_headings_count(self):
        r = AuditResult(url="https://example.com")
        auditor = SEOAuditor(url="https://example.com")
        auditor._check_headings(SAMPLE_HTML, r)
        assert r.headings.total == 4
        assert r.headings.h1_count == 1

    def test_multiple_h1(self):
        r = AuditResult(url="https://example.com")
        auditor = SEOAuditor(url="https://example.com")
        html = "<body><h1>First</h1><h1>Second</h1></body>"
        auditor._check_headings(html, r)
        assert r.headings.h1_count == 2
        assert r.headings.passed is False
        assert len(r.headings.issues) > 0

    def test_skipped_heading_levels(self):
        r = AuditResult(url="https://example.com")
        auditor = SEOAuditor(url="https://example.com")
        html = "<body><h1>One</h1><h3>Jump to H3</h3></body>"
        auditor._check_headings(html, r)
        assert any("Skipped" in i for i in r.headings.issues)


class TestSchemaCheck:
    def test_jsonld_schema(self):
        r = AuditResult(url="https://example.com")
        auditor = SEOAuditor(url="https://example.com")
        auditor._check_schema(SAMPLE_HTML, r)
        assert r.schema.count > 0
        assert r.schema.passed is True

    def test_no_schema(self):
        r = AuditResult(url="https://example.com")
        auditor = SEOAuditor(url="https://example.com")
        auditor._check_schema("<html></html>", r)
        assert r.schema.count == 0
        assert r.schema.passed is False


class TestImageAlt:
    def test_alt_detection(self):
        r = AuditResult(url="https://example.com")
        auditor = SEOAuditor(url="https://example.com")
        auditor._check_image_alt(SAMPLE_HTML, r)
        assert r.image_alt.total == 2
        assert r.image_alt.missing == 1

    def test_no_images(self):
        r = AuditResult(url="https://example.com")
        auditor = SEOAuditor(url="https://example.com")
        auditor._check_image_alt("<html><body><p>No images</p></body></html>", r)
        assert r.image_alt.total == 0
        assert r.image_alt.passed is True


class TestResponsive:
    def test_viewport_present(self):
        r = AuditResult(url="https://example.com")
        auditor = SEOAuditor(url="https://example.com")
        auditor._check_responsive(SAMPLE_HTML, r)
        assert r.responsive.has_viewport is True
        assert r.responsive.passed is True

    def test_viewport_missing(self):
        r = AuditResult(url="https://example.com")
        auditor = SEOAuditor(url="https://example.com")
        auditor._check_responsive("<html></html>", r)
        assert r.responsive.has_viewport is False


class TestIndexability:
    def test_indexable(self):
        r = AuditResult(url="https://example.com")
        auditor = SEOAuditor(url="https://example.com")
        auditor._check_indexable(SAMPLE_HTML, r, None)
        assert r.indexable.indexable is True

    def test_noindex(self):
        r = AuditResult(url="https://example.com")
        auditor = SEOAuditor(url="https://example.com")
        html = '<html><head><meta name="robots" content="noindex"></head></html>'
        auditor._check_indexable(html, r, None)
        assert r.indexable.indexable is False
        assert r.indexable.passed is False


class TestCanonical:
    def test_canonical_found(self):
        r = AuditResult(url="https://example.com/page")
        auditor = SEOAuditor(url="https://example.com/page")
        auditor._check_canonical(SAMPLE_HTML, r)
        assert r.canonical.passed is True
        assert "example.com/page" in r.canonical.href


class TestInternalLinks:
    def test_link_count(self):
        r = AuditResult(url="https://example.com")
        auditor = SEOAuditor(url="https://example.com")
        auditor._check_internal_links(SAMPLE_HTML, r)
        assert r.internal_links.total > 0


class TestOGTags:
    def test_og_tags_extraction(self):
        r = AuditResult(url="https://example.com")
        auditor = SEOAuditor(url="https://example.com")
        auditor._check_og_tags(SAMPLE_HTML, r)
        assert r.og_tags.og_title == "OG Test Title"
        assert r.og_tags.og_image == "https://example.com/og-image.jpg"
        assert r.og_tags.tags_found == 6
        assert r.og_tags.passed is True

    def test_missing_og_tags(self):
        r = AuditResult(url="https://example.com")
        auditor = SEOAuditor(url="https://example.com")
        auditor._check_og_tags("<html></html>", r)
        assert r.og_tags.tags_found == 0
        assert r.og_tags.passed is False


class TestSSL:
    def test_https_detection(self):
        r = AuditResult(url="https://example.com")
        auditor = SEOAuditor(url="https://example.com")
        auditor._check_ssl(r)
        assert r.ssl.is_https is True

    def test_http_detection(self):
        r = AuditResult(url="http://example.com")
        auditor = SEOAuditor(url="http://example.com")
        auditor._check_ssl(r)
        assert r.ssl.is_https is False
        assert r.ssl.passed is False


class TestPerformanceScore:
    def test_perfect_score(self):
        v = CDPVitalsResult(lcp=1.0, cls=0.01, ttfb=0.2)
        auditor = SEOAuditor(url="https://example.com")
        auditor._calc_perf_score(v)
        assert v.perf_score == 100

    def test_poor_score(self):
        v = CDPVitalsResult(lcp=5.0, cls=0.3, ttfb=1.0)
        auditor = SEOAuditor(url="https://example.com")
        auditor._calc_perf_score(v)
        assert v.perf_score < 70
        assert v.passed is False

    def test_moderate_score(self):
        v = CDPVitalsResult(lcp=3.0, cls=0.15, ttfb=0.6)
        auditor = SEOAuditor(url="https://example.com")
        auditor._calc_perf_score(v)
        assert 60 <= v.perf_score <= 90


class TestDataClasses:
    def test_default_values(self):
        assert AuditResult(url="test").title.text == ""
        assert TitleResult().passed is False
        assert CDPVitalsResult().perf_score == 0
        assert OGTagsResult().tags_found == 0

    def test_field_mutation(self):
        t = TitleResult(text="Hello", length=5, status="GOOD", passed=True)
        assert t.text == "Hello"
        assert t.passed is True
