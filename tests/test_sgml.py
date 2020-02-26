import pytest
import json
from edgar.sgml import Sgml, SgmlException
from edgar.dtd import DTD
    
def setup_module(module):
    print('setup_module      module:%s' % module.__name__)

def test_parse_sgml():
    text = '<SEC-DOCUMENT>0001104659-18-050552.txt : 20180808\n<SEC-HEADER>0001104659-18-050552.hdr.sgml : 20180808\n<ACCEPTANCE-DATETIME>20180808170227\n</SEC-HEADER>\n<DOCUMENT>\n<TYPE>4\n<SEQUENCE>1\n<FILENAME>a4.xml\n<DESCRIPTION>4\n<TEXT>\n<XML>\nxml test\n</XML>\n</TEXT>\n</DOCUMENT>\n<DOCUMENT>\n<TYPE>EX-24\n<SEQUENCE>2\n<FILENAME>ex-24.htm\n<DESCRIPTION>EX-24\n<TEXT>\nhtml test\n</TEXT>\n</DOCUMENT>\n</SEC-DOCUMENT>'
    #print(text)

    # convert dict result to json
    sgml = Sgml(text, DTD())
    json_document = json.dumps(sgml.map)
    #print(json_document)

    assert json_document == '{"<SEC-DOCUMENT>": {"<SEC-HEADER>": {"<ACCEPTANCE-DATETIME>": "20180808170227"}, "<DOCUMENT>": [{"<TYPE>": "4", "<SEQUENCE>": "1", "<FILENAME>": "a4.xml", "<DESCRIPTION>": "4", "<TEXT>": {"<XML>": "xml test"}}, {"<TYPE>": "EX-24", "<SEQUENCE>": "2", "<FILENAME>": "ex-24.htm", "<DESCRIPTION>": "EX-24", "<XML>": "", "<TEXT>": "html test"}]}}'

# TODO
# def test_sgml_exception():
# 	try:
# 		# malformed sgml
# 		text = '<SEC-DOCUMENT>00011046500110n<DOCUMENT>\n<TYPE>4\n<SEQUENCE>1\n<FILENAME>a4.xml\n<DESCRIPTION>4\n<TEXT>\n<XML>\nxml test\n</XML>\n</TEXT>\n</DOCUMENT>\n<DOCUMENT>\n<TYPE>EX-24\n<SEQUENCE>2\n<FILENAME>ex-24.htm\n<'
# 		sgml = Sgml(text, DTD())
# 		assert False
# 	except SgmlException:
# 	    assert True