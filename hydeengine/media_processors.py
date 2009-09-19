import os, commands, sys
import fnmatch
from django.template.loader import render_to_string
from django.conf import settings
from file_system import File     


class TemplateProcessor:
    @staticmethod
    def process(resource):
        try:
            rendered = render_to_string(resource.source_file.path, settings.CONTEXT)
            resource.source_file.write(rendered)
        except:
            print >> sys.stderr, \
            "Error while rendering page %s" % \
            resource.url
            raise             
    

## aym-cms code refactored into processors.
class CleverCSS:    
    @staticmethod
    def process(resource):
        import clevercss
        data = resource.source_file.read_all()
        out = clevercss.convert(data)
        resource.source_file.write(out)

class HSS:
    @staticmethod
    def process(resource):
        out_file = File(resource.source_file.path_without_extension + ".css")
        hss = settings.HSS_PATH
        if not hss or not os.path.exists(hss):
            raise ValueError("HSS Processor cannot be found at [%s]" % hss)
        status, output = commands.getstatusoutput(
        u"%s %s -output %s/" % (hss, resource.source_file.path, out_file.parent.path))
        if status > 0: 
            print output
            return None
        resource.source_file.delete()
        out_file.copy_to(resource.source_file.path)
        out_file.delete()
        
        
class YUICompressor:
    @staticmethod
    def process(resource):
        compress = settings.YUI_COMPRESSOR

        if not compress or not os.path.exists(compress):
            return
            
        tmp_file = File(resource.source_file.path + ".z-tmp")
        status, output = commands.getstatusoutput(
        u"java -jar %s %s > %s" % (compress, resource.source_file.path, tmp_file.path))
        if status > 0: 
            print output
        else:
            resource.source_file.delete()
            tmp_file.move_to(resource.source_file.path)