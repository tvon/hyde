# HYDE

0.3 Beta

This document should give enough information to get you up and running. Check the [wiki](http://wiki.github.com/lakshmivyas/hyde) for detailed documentation.

Hyde is a static website generator with the power of Django templates behind it. You can read more about its conception, history and features [here][1] and [here][2].

[1]: http://www.ringce.com/products/hyde/hyde.html
[2]: http://www.ringce.com/blog/2009/introducing_hyde.html


## Basic Installation

The very basic installation of hyde only needs Django, Markdown and pyYAML. More python goodies are needed based on the features you may use.

    sudo easy_install django
    sudo easy_install pyYAML
    sudo easy_install markdown

Get the hyde source by [git cloning](http://github.com/guides/home) this repository.

    sudo python setup.py install


## Running with Hyde

The hyde engine has three entry points:

1. Initializer

        hyde.py -i -s path/to/your/site [-t template_name = default] [-f]
        
    During initialization hyde creates a basic website by copying the specified template (or default). This template contains the skeleton site layout, some content pages and settings.py.
    
    Be careful with the -f setting, though: it will overwrite your website.

2. Generator

        hyde.py -g -s path/to/your/site [-d deploy_dir=path/to/your/site/deploy] [-k]
    
    This will process the content and media and copy the generated website to your deploy directory. 

    If the -k option is specified, hyde will monitor the source folder for changes and automatically process them when the changes are encountered. This option is very handy when tweaking css or markup to quickly check the results. Note of caution: This option does not update listing files or excerpt files. It is recommended that you run -g again before you deploy the website.

3. Web Server

        hyde.py -w -s path/to/your/site [-d deploy_dir=path/to/your/site/deploy]
    
    This will start an instance of a cherrypy server and serve the generated website at localhost:8080.

    
## Site structure

* layout - Template files that are used as base templates for content. None of the files in the layout folder are copied over to the deploy directory.
* content - Any file that is not prefixed with \_, . or suffixed with ~ are processed by running through the template engine.
* media - Contains site media, css, js and images. 
* settings.py - Django and hyde settings.


### Recommended conventions

These conventions will make it easier to configure hyde plugins.

* Prefix files in layout and other template files in content with underscores
* Keep media folder organized by file type[css, flash, js, images].


## Configuring your website

Most of the boilerplate configuration comes as a part of the initialized website. The only setting you _have to_ override is the SITE_NAME setting.


### Media Processors

Media processors are defined in the following format:

    {<folder>:{
        <file_extension_with_dot>:(<processor_module_name1>, <processor_module_name2>)}
    }
    
The processors are executed in the order in which they are defined. The output from the first processor becomes the input of the next.

A \* instead of folder will apply the setting to all folders. There is no wildcard support for folder name yet, \* is just a catch all special case.

File extensions should be specified as .css, .js, .png etc. Again no wildcard support yet. 

Hyde retains the YUI Compressor, Clever CSS and HSS processors from aym-cms.


#### Template Processor 

Template processor allows the use of context variables inside your media files. 


#### YUI Compressor

Runs through the all the files defined in the configuration associated with ``'hydeengine.media_processors.YUICompressor'`` and compresses them. 

[yuic]: http://developer.yahoo.com/yui/compressor/

In the settings file, set ``YUI_COMPRESSOR`` to
be a path to a [YUI Compressor][yuic] jar on your computer.


#### Clever CSS Processor

Runs through the all the files defined in the configuration associated with ``'hydeengine.media_processors.CleverCSS'`` and converts them to css. 

You need to install Clever CSS using ``sudo easy_install CleverCSS`` command for this processor to work.

[clever_css]: http://sandbox.pocoo.org/clevercss/


#### HSS Processor

Runs through the all the files defined in the configuration associated with ``'hydeengine.media_processors.HSS'`` and converts them to css. 

You need to download HSS from [the project website][hss] and set the ``HSS_PATH`` variable to the downloaded path.

[hss]: http://ncannasse.fr/projects/hss


### Content Processors

Content processors are run against all files in the content folder whereas the media processors are run against the media folder. No content processors have been created yet.


## Page Context Variables

Pages can define their own context variables that are passed to the entire template hierarchy when the page is processed. This is accomplished by using a special tag at the top of the content page(after any extends tags you may have).

    {%hyde
        <Your variables>
    %}

Every page in the template hierarchy gets these context variables: ``site`` and ``page``. The site variable contains information about the entire site. The ``page`` variable represents the current content page that is being processed. The variables defined at the top of the content pages using the {% hyde %} tags are available through the page variable as attributes.

On your content pages you can define the page variables using the standard YAML format.

    {%hyde
        title: A New Post
        list: 
            - One
            - Two
            - Three
    %}


## Template Tags

Hyde retains the markdown and syntax template tags from aym_cms. Additionally hyde introduces a few tags for excerpts. These tags are added to the Django built in tags so there is no need for the load statements.


### Markdown

Requires markdown to be installed.

    sudo easy_install markdown

``markdown`` renders the enclosed text as [Markdown](http://daringfireball.net/projects/markdown/) markup.
It is used as follows:

    <p> I love templates. </p>
    {% markdown %}
    Render this **content all in Markdown**.

    >> Writing in Markdown is quicker than
    >> writing in HTML.

    1.  Or at least that is my opinion.
    2.  What about you?
    {% endmarkdown %}


### Textile

Requires textile to be installed.

    sudo easy_install textile

``textile`` renders the enclosed text as [Textile](http://www.textism.com/tools/textile/) markup.
It is used as follows:

    <p> I love templates. </p>
    {% textile %}
    Render this *content all in Textile*.

    bq.  Writing in Textile is also quicker than
         writing in HTML.

    # Or at least that is my opinion.
    # What about you?
    
    {% endtextile %}


### Syntax

Requires Pygments.

    sudo easy_install Pygments

``syntax`` uses Pygments to render the enclosed text with
a code syntax highlighter. Usage is:

    <del>{% load aym %}</del>
    <p> blah blah blah </p>
    {% syntax objc %}
    [obj addObject:[NSNumber numberWithInt:53]];
    return [obj autorelease];
    {% endsyntax %}

They are both intended to make writing static content
quicker and less painful.


### Hyde

The ``{%hyde%}`` tag is used for the page variables, as a template tag all it does is swallow the contents and prevent them from showing up in the html. The even safer approach is to define this tag outside of all blocks so that it is automatically ignored.


### Excerpt

The ``{%excerpt%}{%endexcerpt%}`` tag decorates the output with html comments that mark the excerpt area. Excerpts marked in this manner can be referenced in other pages using the ``{%render_excerpt%}`` or the ``{%latest_excerpt%}`` tag.


### Render Excerpt

Render Excerpt takes a page variable and optional number of words argument to render the excerpt from the target page.


### Latest Excerpt

Latest Excerpt takes a content folder path and optional number of words as input. It parses through the content pages looking for page variables named ``created`` and gets the page with the maximum value and renders the excerpt from that page.


### Article

The ``{%article%}{%endarticle%}`` tags mark content enclosed in them to be included as inline content when the atom feed is generated.


### Render Article

Render Article renders the html content bracketed by the `{%article%}` tag from the given page.


### Typogrify

To enable Typogrify, use ``{% filter typogrify %}`` in your code. Typogrify is "a collection of Django template filters that help prettify your web typography by preventing ugly quotes and widows", according to the [project web site][typogrify_site]. It is automatically enabled in the default template.

[typogrify_site]:http://code.google.com/p/typogrify/


## Base Templates

There are two layouts currently available: default and simple.

The default site layout contains templates for basic site structure, navigation, breadcrumbs, listing, posts and Atom feed and a very basic stylesheet. 


# Examples

The [Ringce][ringce] website source is available as a reference implementation.

[ringce]:http://github.com/lakshmivyas/ringce/tree/master


# CONTRIBUTORS

- [lakshmivyas](http://github.com/lakshmivyas)
- [joshrosen](http://github.com/JoshRosen)
- [Harry Lachenmayer](http://github.com/h3yl9r)
- [Kailoa Kadano](http://github.com/kailoa)
- [Tom von Schwerdtner](http://github.com/tvon)
- [montecristo](http://github.com/montecristo)
- [Valentin Jacquemin](http://github.com/poxd)
- [Johannes Reinhard](http://github.com/SpeckFleck)