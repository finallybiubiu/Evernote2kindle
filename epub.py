#coding:utf-8

import os
import time
import hashlib
import xml.etree.ElementTree as ET

templates_path = os.path.join(os.getcwd(),'templates')

# 重写 _serialize_xml 方法，避免 <img> 被转义
def CDATA(text):
    element = ET.Element('![CDATA[')
    element.text = text
    return element
ET._original_serialize_xml = ET._serialize_xml
def _serialize_xml(write, elem, encoding, qnames, namespaces):
    if elem.tag == '![CDATA[':
        write("%s" % elem.text)
        return
    return ET._original_serialize_xml(write, elem, encoding, qnames, namespaces)
ET._serialize_xml = ET._serialize['xml'] = _serialize_xml
# 重写完毕 == http://stackoverflow.com/questions/174890/how-to-output-cdata-using-elementtree 

class article():

	def __init__(self,title,ctx):
		self.title = title
		self.ctx = ctx

class EpubBook():

	# 初始化的时候会建立文件夹，以便添加img
	def __init__(self,name):
		self.name = name	# 书名
		self.date = str(time.asctime())
		self.identifier = 'urn:uuid:'+mysha1(self.date)
		self.lang = 'zh-CN'
		self.creator = 'kzzhr'
		self.publisher = 'kzzhr'
		self.subject = 'ZeroTag'
		self.description = 'This is a new book'
		self.book = []
		self.imgs = []

		os.system('rm -rf %s' % self.name)
		os.mkdir(self.name)

		pass

	# 生成一个 Epub 文件夹
	def Save(self):

		os.chdir(self.name)
		print os.getcwd()

		# 复制 templates 文件
		os.mkdir('META-INF')
		copyFile(os.path.join(templates_path,'META-INF','container.xml') , os.path.join('META-INF','container.xml'))
		copyFile(os.path.join(templates_path,'content.opf') , 'content.opf')
		copyFile(os.path.join(templates_path,'cover.jpg') , 'cover.jpg')
		copyFile(os.path.join(templates_path,'cover.xhtml') , 'cover.xhtml')
		copyFile(os.path.join(templates_path,'toc.ncx') , 'toc.ncx')
		copyFile(os.path.join(templates_path,'toc.xhtml') , 'toc.xhtml')
		copyFile(os.path.join(templates_path,'ch0.xhtml') , 'ch0.xhtml')
		copyFile(os.path.join(templates_path,'mimetype') , 'mimetype')

		ET.register_namespace('', 'http://www.idpf.org/2007/opf')

		# content.opf
		# --------------
		dom = ET.parse('content.opf')
		root = dom.getroot()
		m = root[0]
		m.getchildren()[0].text = self.name
		m.getchildren()[1].text = self.date
		m.getchildren()[2].text = self.identifier
		m.getchildren()[3].text = self.lang
		m.getchildren()[5].text = self.creator
		m.getchildren()[6].text = self.publisher
		m.getchildren()[7].text = self.subject
		m.getchildren()[8].text = self.description

		# 文章清单 manifest
		m = root[1]
		for i in range(1,len(self.book)+1):
			e = ET.Element('item', {'href':'ch%d.xhtml'%i,'id':'ch%d_xhtml'%i,'media-type':'application/xhtml+xml'})
			m.append(e)
		# 添加图片
		# for i in range(0, len(self.imgs)):
		# 	tp = imgType(self.imgs[0])
		# 	e = ET.Element('item', {'id':'img%d'%i,'href':self.imgs[i],'media-type':'image/%s'%tp})
		# 	m.append(e)

		# spine
		sp = root[2]
		for i in range(1, len(self.book) +1 ):
			e = ET.Element('itemref',{'idref':'ch%d_xhtml'%i})
			sp.append(e)

		dom.write('content.opf', encoding='utf-8', xml_declaration=True)

		# toc.ncx
		# -------------
		dom = ET.parse('toc.ncx')
		root = dom.getroot()
		head = root[0]
		head[0].set('content',self.identifier)
		nav = root[2]
		for i in range(1,len(self.book)+1):
			np = ET.Element('navPoint',{'id':'navPoint-%d'%i})
			nl = ET.Element('navLabel')
			nt = ET.Element('text')
			nt.text = self.book[i-1].title
			nl.append(nt)
			nc = ET.Element('content',{'src':'ch%d.xhtml'%i})
			np.append(nl)
			np.append(nc)
			nav.append(np)

		dom.write('toc.ncx', encoding='utf-8', xml_declaration=True)

		# toc.xhtml
		# -------------
		dom = ET.parse('toc.xhtml')
		root = dom.getroot()
		body = root[1]
		for i in range(1, len(self.book)+1 ):
			li = ET.Element('li')
			a = ET.Element('a',{'href':'ch%d.xhtml'%i})
			a.text = self.book[i-1].title
			li.append(a)
			body.append(li)

		dom.write('toc.xhtml', encoding='utf-8')
		
		# chX.xhtml
		# -------------
		for i in range(1, len(self.book)+1 ):
			dom = ET.parse('ch0.xhtml')
			root = dom.getroot()
			body = root[1]
			body[0].text = self.book[i-1].title
			div = ET.Element('div')
			div.append(CDATA(self.book[i-1].ctx))
			body.append(div)
			dom.write('ch%d.xhtml'%i, 'utf-8')

		print '[Done]'
		os.chdir('../')

	def Pack2Epub(self):
		filename = self.name+'.epub'
		os.system('rm -rf '+filename)
		os.chdir(self.name)
		os.system('zip -r '+ filename+' *')
		os.system('mv '+ filename+' ../'+filename)
		os.chdir('../')
		# os.system('rm -rf '+self.name)

	def Save2Epub(self):
		self.Save()
		self.Pack2Epub()

	def E2Mobi(self):
		os.system('kindlegen %s.epub' % self.name)

	# 使用 Calibre 的 ebook-convert 命令
	def Calibre_Convert(self, name):
		print '将调用 Calibre 的 ebook-convert 转换，请确保已安装 Calibre 并配置好 $PATH'
		os.system('ebook-convert %s.epub %s' % ( self.name, name ))

	# 把 /a/b/c.jpg 保存到 bookname/c.jpg
	# 绝对路径
	def newImg(self, path):
		s = path
		if s.rfind('/') != -1:
			s = s[s.rfind('/')+1:]
		os.system('cp %s %s' % ( path, os.path.join(self.name, s) ) )
		# self.imgs.append(s)

def imgType(s):
	return s[s.find('.')+1:]

# 复制文本文件
def copyFile(url1,url2):
	f1 = open(url1)
	f2 = open(url2,'w')
	f2.write(f1.read())
	f1.close()
	f2.close()

# 新建文本文件
def newFile(filename, ctx):
	fo = open(filename,'w')
	fo.write(ctx)
	fo.close()

# 加密
def mysha1(s):
	sha1obj = hashlib.sha1()
	sha1obj.update(str(s))
	return sha1obj.hexdigest()

# 示例
if __name__ == '__main__':

	# 新建实例
	b = EpubBook('my_test_book')
	b.subject = 'one'
	b.description = 'the first book by epub.py'

	# 添加文章
	b.book.append(article('book1', '下面是一张图片<img src="cover.jpg"/>'))
	b.book.append(article('book2', 'ctx2<img src="DeepinScreenshot20150116205054.png"/>'))
	b.book.append(article('book3', 'ctx3'))

	# 添加图片
	b.newImg('/home/zhr/Desktop/DeepinScreenshot20150116205054.png')

	# 保存 & 打包
	b.Save2Epub()
	# 使用 Calibre 的 ebook-convert 打包
	b.Calibre_Convert('my_test_book.mobi')
	# .mobi
	# b.E2Mobi()

