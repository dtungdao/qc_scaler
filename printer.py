from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch, cm
from reportlab.lib.pagesizes import letter, A4, A3, A2, A1
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.pdfgen import canvas

def DataToPdfFunc(data, file_name, col_width, title=None, des=None):
	story = []
	doc = SimpleDocTemplate(file_name, pagesize=A4, botMargin=inch/6, topMargin=inch/6, leftMargin=inch/4, rightMargin=inch/4)
	styleH = getSampleStyleSheet()['Heading1']	
	styleP = getSampleStyleSheet()['BodyText']	
	
	if( title ):
		story.append(Paragraph(title, styleH))
		story.append(Spacer(1, 0.25 * inch))
		
	if( des ):
		story.append(Paragraph(title, styleP))
		story.append(Spacer(1, 0.25 * inch))
	
	table = Table(data, colWidths=[w*inch for w in col_width], hAlign='LEFT')
	table.setStyle(TableStyle([
			('FONT', (0, 0), (-1, 0), 'Helvetica-Bold'),
			('ALIGN', (0, 0), (-1, 0), 'CENTER'),
			('INNERGRID', (0, 0), (-1, -1), 0.50, colors.black),
			('BOX', (0,0), (-1,-1), 0.25, colors.black),
			]))
	story.append(table)
	
	doc.build(story)
	
def TextToPdf(text, file_name):
	story = []
	doc = SimpleDocTemplate(file_name, pagesize=A4, botMargin=inch/6, topMargin=inch/6, leftMargin=inch/4, rightMargin=inch/4)
	style = getSampleStyleSheet()['BodyText']
	
	for line in text.split("\n"):
		story.append(Paragraph(line, style))
		
	doc.build(story)