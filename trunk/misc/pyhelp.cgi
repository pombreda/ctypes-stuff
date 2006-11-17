#!/usr/bin/env python

# Thomas Heller, 2002-04-04
#
# A script to look up keywords in the Python manuals index
#
# 2006/11/17
#   Fixed a html inject issue by using cgi.escape in the correct places.
#   Thanks to Bernd Essl for the heads-up.
#
# 2006/10/27
#   Moved to SVN repository at http://ctypes-stuff.googlecode.com/svn/trunk/misc/pyhelp.cgi
#   Updated for Python 2.5.
#
################################################################
#
# Revision 1.22  2003/08/07 17:33:16  thomas
# Revert back to the state of 1.19, added Python 2.3, and changed to 2.3 as default.
#
# Revision 1.19  2002/04/15 19:28:34  thomas
# the -b flag was missing from the usage printout.
#
# Revision 1.18  2002/04/12 07:33:27  thomas
# Assume charset=iso-8859-1.
#
# Revision 1.17  2002/04/11 14:18:19  thomas
# The HTML trailer was missing for format=brief.
#
# Instead of using a stylesheet (which one?) to format the links in
# brief mode, use <small></small>.
#
# Revision 1.16  2002/04/11 14:04:03  thomas
# Show unlimited number of results. Links now have a class="text-link",
# but this has no effect, because no stylesheet is specified.
#
# Revision 1.15  2002/04/11 13:24:52  thomas
# Hehe. This works in Mark's Python sidebar.
#
# Revision 1.14  2002/04/11 11:30:01  thomas
# brief wasn't.
#
# Revision 1.13  2002/04/11 11:28:11  thomas
# Download link now works.
#
# Revision 1.12  2002/04/11 10:49:39  thomas
# Removed target="_content" again because it opens the link in a new
# browser window. If it is needed, it should be triggered by a new parameter
# or maybe by format=brief.
#
# Revision 1.11  2002/04/11 07:35:46  thomas
# Also show the result page if only one hit found.
# Display a link to download this script (in the CGI version).
# Remove bogus charset value from Content-type.
#
# As suggested by Mark Hammond, the parameter format=brief suppresses
# all output except the result list. Also added target="_content" to the
# generated links.
#
# Revision 1.10  2002/04/08 14:33:32  thomas
# This version has been posted to Python's tracker on SF.
# We'll see what kind of feedback we get...
#
# Revision 1.9  2002/04/05 19:45:14  thomas
# More text in the CGI HTML page.
#
# Revision 1.5  2002/04/05 19:33:19  thomas
# More HTML code.
#
# Revision 1.4  2002/04/05 16:15:07  thomas
# Valid HTML 4.01. charset is utf-8, is this correct?
#
# Revision 1.3  2002/04/05 14:51:26  thomas
# Now also works as CGI script (has even been tested on starship)
#
# Revision 1.2  2002/04/05 14:49:34  thomas
# Pickles the found links to disk instead of downloading the index pages
# everytime.
#
# Revision 1.1  2002/04/05 14:48:15  thomas
# First version, posted to python-dev asking for comments.
#

import htmllib, formatter, re
import urllib, webbrowser
import sys, os


if __name__ == '__main__':
    __file__ = sys.argv[0]

__version__ = "$Rev$"[6:-2]


DOCMAP = {
    "2.0": "http://www.python.org/doc/2.0/",
    "2.1": "http://www.python.org/doc/2.1/",
    "2.2": "http://www.python.org/doc/2.2/",
    "2.3": "http://www.python.org/doc/2.3/",
    "2.4": "http://www.python.org/doc/2.4/",
    "2.5": "http://www.python.org/doc/2.5/",
    "current": "http://docs.python.org/",
    "devel": "http://docs.python.org/dev/",

# Can alternatively use local documentation!
##    "local": "file:c:/python22/doc/",
##    "2.2": "file:c:/python22/doc/",
##    "2.1": "file:c:/python21/doc/",
##    "2.0": "file:c:/python20/doc/",
    }
INDEXPAGE = "genindex.html" # XXX Only valid for 2.0 and above
SECTIONS = "api/ ref/ lib/".split()
DEFAULT_VERSION = "2.5"

# modified from an example in the eff-bot guide to the Python Library...
class Parser(htmllib.HTMLParser):
    def __init__(self, url, verbose=0):
        self.anchors = {}
        f = formatter.NullFormatter()
        htmllib.HTMLParser.__init__(self, f, verbose)
        self.last_text = ""
        self.url = url

    def anchor_bgn(self, href, name, type):
        self.save_bgn()
        self.anchor = self.url + href

    def anchor_end(self):
        text = self.save_end().strip()
        if text == "[Link]" and self.last_text:
            text = self.last_text
        if self.anchor and text:
            self.anchors[text] = self.anchors.get(text, []) + [self.anchor]
            self.last_text = text


def get_anchors(version, rebuild):
    # returns a list of (topic, url) pairs
    # if rebuild is true, the index is rebuilt
    # if rebuild is false, the index is rebuild if not present
    import cPickle

    baseurl = DOCMAP[version]

    pathname = baseurl
    for char in ":/\\":
        pathname = pathname.replace(char, "-")

    pathname = pathname + version + ".index"

    if not rebuild:
        try:
            file = open(pathname, "rb")
            data = cPickle.load(file)
            return data
        except (IOError, cPickle.PickleError):
            pass

    a = []

    for sec in SECTIONS:
        print "Downloading", baseurl + sec + INDEXPAGE
        file = urllib.urlopen(baseurl + sec + INDEXPAGE)
        html = file.read()
        file.close()

        print "Parsing", baseurl + sec
        p = Parser(baseurl + sec)
        p.feed(html)
        p.close()

        a.extend(p.anchors.items())

    try:
        file = open(pathname, "wb")
    except IOError, detail:
	print detail
        print os.path.abspath("index" + version)
    else:
	cPickle.dump(a, file, 1)
    return a

def find_topics(topic, version, regexp, rebuild):
    v = []

    if regexp:
	pat = re.compile(topic)
        for key, urls in get_anchors(version, rebuild):
            if pat.match(key):
                for url in urls:
                    v.append((key, url))
    else:
        
        for key, urls in get_anchors(version, rebuild):
            if key.startswith(topic):
                for url in urls:
                    v.append((key, url))
    v.sort()
    return v

def get_tempdir():
    import tempfile
    tempfile.mktemp()
    return tempfile.tempdir

def help(topic, version="2.3", regexp=0, rebuild=0):
    baseurl = DOCMAP[version]

    v = find_topics(topic, version, regexp, rebuild)

    if len(v) == 0:
        print "Not found"
## This won't work, because the webbrowser doesn't jump to file
## urls ending in ...#spam !
##    elif len(v) == 1: # only one topic found, display directly
##        webbrowser.open(v[0][1])
    else:
        # create a temporary HTML page displaying links to the
        # search results. Unfortunately the file cannot be deleted,
        # because it may still be needed by the browser.
        path = os.path.join(get_tempdir(), "pyhelp-results.html")
        print path
        file = open(path, "w")
        file.write("<HTML><BODY>\n")
        if regexp:
            file.write("<p><b>%d regexp search results for '%s':</b></p>\n" \
                       % (len(v), topic))
        else:
            file.write("<p><b>%d search results for '%s':</b></p>\n" \
                       % (len(v), topic))

        for href, url in v:
            file.write("<b><a href=%s>%s</a></b><br>\n" % (url, href))
        url = "http://starship.python.net/crew/theller/cgi-bin/pyhelp.cgi"
        file.write('''<hr>Repeat this <a href="%s?keyword=%s&version=%s%s">
search</a> on the web''' % (url, topic, version, regexp and "&regexp=on" or ""))
        file.write("</BODY></HTML>\n")
        file.close()
        webbrowser.open(path)

def cgi_help():
    import cgi, cgitb
    cgitb.enable()

    form = cgi.FieldStorage()

    if form.has_key("action") and form["action"].value == "download":
        print "Content-type: text/plain"
        print
        data = open(__file__).read()
        sys.stdout.write(data)
        return

    brief = 0
    if form.has_key("format") and form["format"].value == "brief":
        brief = 1

    # This assumes the charset the Python docs are written in...
    print "Content-type: text/html; charset=iso-8859-1"
    print
    print '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">'
    print "<HTML><HEAD><TITLE>Search Python Manual</TITLE></HEAD><BODY>"

    if not brief:
        print "<form action=%s method=GET>" % os.path.basename(__file__)
        print "<b>Python Keyword</b>"
        if form.has_key("keyword"):
            print '<input name="keyword" value="%s">' % cgi.escape(form["keyword"].value, True)
        else:
            print '<input name="keyword">'
        print '<input type="submit" value="search">'

        print "Documentation version:"
        print '<select name="version">'
        for vers in ["current", "2.5", "2.4", "2.3", "2.2", "2.1", "2.0", "devel"]:
            if form.has_key("version") and form["version"].value == vers:
                print '<option value="%s" SELECTED>%s' % (vers, vers)
            else:
                print '<option value="%s">%s' % (vers, vers)
        print '</select>'

        if form.has_key("regexp") and form["regexp"].value:
            print '<input type="checkbox" name="regexp" CHECKED>Regular Expression'
        else:
            print '<input type="checkbox" name="regexp">Regular Expression'

        print "</form>"


    version = "2.4"
    if form.has_key("version"):
        version = form["version"].value
    regexp = 0
    if form.has_key("regexp"):
        regexp = form["regexp"].value

    if form.has_key("keyword"):
	baseurl = DOCMAP[version]
	v = find_topics(form["keyword"].value, version=version,
                        regexp=regexp, rebuild=0)

        if not brief:
            print "<hr>"
            topic = form["keyword"].value
            print "<p><b>%d search results for '%s':</b></p>" % (len(v), cgi.escape(topic))
            for topic, url in v:
                print '<b><a href="%s">%s</a><br></b>\n' % (url, topic)
        else:
            print '<small>'
            # Hm. Limit the number of results? Maybe the next parameter...
            for topic, url in v:
                # Next hm. class=... has no effect. Which stylesheet to use?
                print '<a class="text-link" href="%s" target="_content">%s</a><br>\n' \
                      % (url, cgi.escape(topic))
            print '</small>'

    if not brief:
        print '''<hr>
This script looks up keywords in the Python
<b><a href="http://www.python.org/doc/current/lib/lib.html">Library Reference</a></b>,
<b><a href="http://www.python.org/doc/current/ref/ref.html">Language Reference</a></b>,
and <b><a href="http://www.python.org/doc/current/api/api.html">Python/C API</a></b>
manuals.<br>
For full text searches better consult the usual web search engines.
'''
        print '''<hr><a href="http://validator.w3.org/check/referer"><img border="0"
src="http://www.w3.org/Icons/valid-html401"
alt="Valid HTML 4.01!" height="31" width="88"></a>
<a href="http://www.python.org/"><img border="0"
src="http://www.python.org/pics/PythonPoweredSmall.gif"
alt="Powered by Python" width="55" height="22"></a>
'''
        print '''
<br><small>Download this script/module:<a href="%s?action=download">%s</a>, version %s.
<br>Please send any comments/suggestions to
<a href="mailto:theller@ctypes.org">Thomas Heller</a>.</small>
''' % (os.path.basename(__file__), os.path.basename(__file__), __version__)

    print "</BODY></HTML>"

def main():
    os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))
    if os.environ.has_key("SCRIPT_NAME"):
	cgi_help()
	sys.exit()

    import getopt
    try:
        opts, args = getopt.getopt(sys.argv[1:], "v:rb",
                                   ["version=", "useregexp", "rebuild"])
    except getopt.GetoptError:
        print "Usage: %s [-b] [-r] [-v version] topic" % sys.argv[0]
        sys.exit(1)

    version = DEFAULT_VERSION
    regexp = 0
    rebuild = 0

    for o, a in opts:
        if o in ("-v", "--version"):
            if a not in DOCMAP.keys():
                print "version must be one of %s" % ", ".join(DOCMAP.keys())
                sys.exit(1)
            version = a
        if o in ("-r", "--useregexpg"):
            regexp = 1
        if o in ("-b", "--rebuild"):
            rebuild = 1

    if len(args) != 1:
        print "Usage: %s [-b] [-r] [-v version] topic" % sys.argv[0]
        sys.exit(1)
    os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))

    help(args[0], version, regexp, rebuild)

if __name__ == '__main__':
    main()

# -- EOF --
