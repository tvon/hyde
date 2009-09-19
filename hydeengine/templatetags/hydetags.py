from django import template
from django.conf import settings
from django.template import Template
from django.template.loader import render_to_string
from django.template.defaultfilters import truncatewords_html
from django.template import Library
from django.utils.safestring import mark_safe
from hydeengine.file_system import Folder
import re
import string
import os
import operator
from datetime import datetime
from datetime import timedelta
from hydeengine.file_system import Folder 


marker_start = "<!-- Hyde::%s::Begin -->\n"
marker_end = "<!-- Hyde::%s::End -->\n"

register = Library()

class HydeContextNode(template.Node):
    def __init__(self): 
        pass
    
    def render(self, context):
        return ""
        
@register.tag(name="hyde")
def hyde_context(parser, token):
    return HydeContextNode()

@register.tag(name="excerpt")
def excerpt(parser, token):
    nodelist = parser.parse(('endexcerpt',))
    parser.delete_first_token()
    return BracketNode("Excerpt", nodelist)
    
@register.tag(name="article")
def excerpt(parser, token):
    nodelist = parser.parse(('endarticle',))
    parser.delete_first_token()
    return BracketNode("Article", nodelist)

class BracketNode(template.Node):
    def __init__(self, marker, nodelist):
        self.nodelist = nodelist
        self.marker = marker

    def render(self, context):
        rendered_string = self.nodelist.render(context)
        return marker_start % self.marker +\
                rendered_string + \
                marker_end % self.marker


class LatestExcerptNode(template.Node):
    def __init__(self, path, words = 50):
        self.path = path
        self.words = words
        
    def render(self, context):
        sitemap_node = None
        if not self.words == 50:
            self.words = self.words.render(context)
        self.path = self.path.render(context).strip('"')
        sitemap_node = context["site"].find_node(Folder(self.path))
        if not sitemap_node:
            sitemap_node = context["site"]
        def later(page1, page2):
            return (page1, page2)[page2.created > page1.created]
        page = reduce(later, sitemap_node.walk_pages())
        rendered = None
        rendered = render_to_string(str(page), context)
        excerpt_start = marker_start % "Excerpt"
        excerpt_end = marker_end % "Excerpt"
        start = rendered.find(excerpt_start)
        if not start == -1:
            context["latest_excerpt_url"] = page.url
            context["latest_excerpt_title"] = page.title
            start = start + len(excerpt_start)
            end = rendered.find(excerpt_end, start)
            return truncatewords_html(rendered[start:end], self.words)
        else:
            return ""                    
            
class RecentPostsNode(template.Node):
    def __init__(self, var='recent_posts', count=5, node=None):
        self.var = var
        self.count = count        
        self.node=node                    
                
    def render(self, context):             
        if not self.node:
            self.node = context['site']
        else:
            self.node = self.node.resolve(context)    
            
        if not self.count == 5:
            self.count = self.count.render(context)    
            
        if not self.var == 'recent_posts':
            self.var = self.var.render(context) 

        if (not hasattr(self.node, 'complete_page_list') or 
            not self.node.complete_page_list):    
            complete_page_list = sorted(
                self.node.walk_pages(),
                key=operator.attrgetter("created"), reverse=True)
            complete_page_list = filter(lambda page: page.display_in_list, 
                                            complete_page_list)    
            self.node.complete_page_list = complete_page_list

        context[self.var] = self.node.complete_page_list[:int(self.count)]  
        return ''
        
            
@register.tag(name="recent_posts")
def recent_posts(parser, token):
    tokens = token.split_contents()
    count = 5
    node = None          
    var = 'recent_posts'        
    if len(tokens) > 1:
        var = Template(tokens[1])    
    if len(tokens) > 2:
        count = Template(tokens[2])
    if len(tokens) > 3:
        node = parser.compile_filter(tokens[3])        
    return RecentPostsNode(var, count, node)            
            
class PostsLoader(template.Node):
    """
    Loads the list posts (pages in the CONTENT_BLOG_DIR node) until reaching the nbPosts limit. 
    By default, no limit.
    """
    def __init__(self, nbPosts=None):
        self.nbPosts=nbPosts
        
    def render(self, context):
        site = context['site']
        context['blog']['posts'] = []
        nbPosts = self.nbPosts
        for i, post in enumerate(site.find_node(Folder(settings.BLOG_DIR)).walk_pages()):
            if post.listing == False:
                if nbPosts != None and i >= nbPosts:
                    break;
                context['blog']['posts'].append(post)
        return ""
            
@register.tag(name="load_posts")
def load_posts(parser, token):
    tokens = token.split_contents()
    nbPosts = None
    if len(tokens) > 1:
        nbPosts = Template(tokens[1])
    return PostsLoader(nbPosts)
        
@register.tag(name="latest_excerpt")
def latest_excerpt(parser, token):
    tokens = token.split_contents()
    path = None
    words = 50
    if len(tokens) > 1:
        path = Template(tokens[1])
    if len(tokens) > 2:
        words = Template(tokens[2])
    return LatestExcerptNode(path, words)

@register.tag(name="render_excerpt")    
def render_excerpt(parser, token):
    tokens = token.split_contents()
    path = None
    words = 50
    if len(tokens) > 1:
        path = parser.compile_filter(tokens[1])
    if len(tokens) > 2:
        words = Template(tokens[2])
    return RenderExcerptNode(path, words)

@register.tag(name="render_article")    
def render_article(parser, token):
    tokens = token.split_contents()
    path = None
    if len(tokens) > 1:
        path = parser.compile_filter(tokens[1])
    return RenderArticleNode(path)
    
class RenderExcerptNode(template.Node):
    def __init__(self, page, words = 50):
        self.page = page
        self.words = words

    def render(self, context):
        if not self.words == 50:
            self.words = self.words.render(context)
        page = self.page.resolve(context)
        context["excerpt_url"] = page.url
        context["excerpt_title"] = page.title
        rendered = get_bracketed_content(context, page, "Excerpt")
        return truncatewords_html(rendered, self.words)
        

class RenderArticleNode(template.Node):
    def __init__(self, page):
        self.page = page

    def render(self, context):
        page = self.page.resolve(context)
        return get_bracketed_content(context, page, "Article")

            
def get_bracketed_content(context, page, marker):
        rendered = None
        original_page = context['page']
        context['page'] = page
        rendered = render_to_string(str(page), context)
        context['page'] = original_page
        bracket_start = marker_start % marker
        bracket_end = marker_end % marker
        start = rendered.find(bracket_start)
        if not start == -1:
            start = start + len(bracket_start)
            end = rendered.find(bracket_end, start)
            return rendered[start:end]
        return ""


@register.filter
def value_for_key(dictionary, key):
    if not dictionary:        
        return ""
    if not dictionary.has_key(key):        
        return ""
    value = dictionary[key]
    return value

@register.filter
def xmldatetime(dt):
    if not dt:
        dt = datetime.now()
    zprefix = "Z"
    tz = dt.strftime("%z")
    if tz:
        zprefix = tz[:3] + ":" + tz[3:]
    return dt.strftime("%Y-%m-%dT%H:%M:%S") + zprefix

@register.filter
def remove_date_prefix(slug, sep="-"):
    expr = sep.join([r"\d{2,4}"]*3 + ["(.*)"]) 
    match = re.match(expr, slug)
    if not match:
        return slug
    else:
        return match.group(0)

@register.filter
def unslugify(slug):
    words = slug.replace("_", " ").\
                    replace("-", " ").\
                        replace(".", "").split()
                        
    return ' '.join(map(lambda str: str.capitalize(), words))

@register.tag(name="hyde_listing_page_rewrite_rules")
def hyde_listing_page_rewrite_rules(parser, token):
    """Prints the Apache Mod_Rewrite RewriteRules for clean urls for pages in
    LISTING_PAGE_NAMES.  These rules are designed to be placed in a .htaccess
    file; they have not been tested inside of httpd.conf

    This only generates RewriteRules; it does not enable url rewriting or set
    RewriteBase.
    """
    return RenderHydeListingPageRewriteRulesNode()


LPN_REWRITE_RULE = string.Template(\
r"""
RewriteCond %{REQUEST_FILENAME}/${name}.html -f
RewriteRule ^(.*) $1/${name}.html
"""
)

class RenderHydeListingPageRewriteRulesNode(template.Node):
    def render(self, context):
        if not settings.LISTING_PAGE_NAMES:
            return ''
        rules = [] # for LISTING_PAGE_NAMES listings
        for name in settings.LISTING_PAGE_NAMES:
            rules.append(LPN_REWRITE_RULE.safe_substitute( \
                {'name': name}))
        return \
            "###  BEGIN GENERATED REWRITE RULES  ####\n" \
          + ''.join(rules) \
          + "\n####  END GENERATED REWRITE RULES  ####"
