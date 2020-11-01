import logging
import os
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from mkdocs.config import config_options

from .drivers.headless_chrome import HeadlessChromeDriver
from .template import Template


def _normalize(text: str) -> str:
    if text:
        return BeautifulSoup(text, 'html.parser').text
    return None


class Options(object):

    config_scheme = (
        ('enabled_if_env', config_options.Type(str)),

        ('verbose', config_options.Type(bool, default=False)),
        ('debug_html', config_options.Type(bool, default=False)),
        ('show_anchors', config_options.Type(bool, default=False)),

        ('output_path', config_options.Type(str, default="pdf/document.pdf")),
        ('theme_handler_path', config_options.Type(str, default=None)),

        ('author', config_options.Type(str, default=None)),
        ('copyright', config_options.Type(str, default=None)),

        ('cover', config_options.Type(bool, default=True)),
        ('custom_template_path',
            config_options.Type(str, default="templates")),
        ('cover_title', config_options.Type(str, default=None)),
        ('cover_subtitle', config_options.Type(str, default=None)),
        ('cover_logo', config_options.Type(str, default=None)),

        ('toc_title', config_options.Type(str, default="Table of contents")),
        ('heading_shift', config_options.Type(bool, default=True)),
        ('toc_level', config_options.Type(int, default=2)),
        ('ordered_chapter_level', config_options.Type(int, default=3)),
        ('excludes_children', config_options.Type(list, default=[])),

        ('exclude_pages', config_options.Type(list, default=[])),
        ('convert_iframe', config_options.Type(list, default=[])),
        ('two_columns_level', config_options.Type(int, default=0)),

        ('render_js', config_options.Type(bool, default=False)),
        ('headless_chrome_path',
            config_options.Type(str, default='chromium-browser'))
    )

    def __init__(self, local_config, config, logger: logging):
        self.strict = True if config['strict'] else False

        self.verbose = local_config['verbose']
        self.debug_html = local_config['debug_html']
        self.show_anchors = local_config['show_anchors']

        self.output_path = local_config.get('output_path', None)
        self.theme_handler_path = local_config.get('theme_handler_path', None)

        # Author and Copyright
        self._author = _normalize(local_config['author'])
        if not self._author:
            self._author = _normalize(config['site_author'])

        self._copyright = _normalize(local_config['copyright'])
        if not self._copyright:
            self._copyright = _normalize(config['copyright'])

        # Cover
        self.cover = local_config['cover']
        if self.cover:
            self._cover_title = local_config['cover_title'] \
                if local_config['cover_title'] else config['site_name']
            self._cover_subtitle = local_config['cover_subtitle']

        # path to custom template 'cover.html' and custom scss 'styles.scss'
        self.custom_template_path = local_config['custom_template_path']

        # TOC and Chapter heading
        self.toc_title = _normalize(local_config['toc_title'])
        self.heading_shift = local_config['heading_shift']
        self.toc_level = local_config['toc_level']
        self.ordered_chapter_level = local_config['ordered_chapter_level']
        self.excludes_children = local_config['excludes_children']

        # Page
        self.exclude_pages = local_config['exclude_pages']
        self.convert_iframe = local_config['convert_iframe']

        self.two_columns_level = local_config['two_columns_level']

        # ...etc.
        self.js_renderer = None
        if local_config['render_js']:
            self.js_renderer = HeadlessChromeDriver.setup(
                local_config['headless_chrome_path'], logger)

        # Theming
        self.theme_name = config['theme'].name
        if not self.theme_handler_path:
            # Read from global config only if plugin config is not set
            self.theme_handler_path = config.get('theme_handler_path', None)

        # Template handler(Jinja2 wrapper)
        self._template = Template(self, config)

        if self.cover:
            self._logo_url = self._url_for(local_config['cover_logo'], config)

        # for system
        self._logger = logger

    def _url_for(self, href: str, config) -> str:
        if not href:
            return None

        # Check for URL(eg. 'https://...')
        target_url = urlparse(href)
        if target_url.scheme or target_url.netloc:
            return href

        # Search image file in below directories:
        dirs = [
            self.custom_template_path,
            getattr(config['theme'], 'custom_dir', None),
            config['docs_dir'],
            '.'
        ]

        for d in dirs:
            if not d:
                continue
            path = os.path.abspath(os.path.join(d, href))
            if os.path.isfile(path):
                return 'file://' + path

        return None

    @property
    def author(self) -> str:
        return self._author

    @property
    def copyright(self) -> str:
        return self._copyright

    @property
    def cover_title(self) -> str:
        return self._cover_title

    @property
    def cover_subtitle(self) -> str:
        return self._cover_subtitle

    @property
    def logo_url(self) -> str:
        return self._logo_url

    @property
    def logger(self) -> logging:
        return self._logger

    @property
    def template(self) -> Template:
        return self._template
