import sys, time, codecs, datetime
import win32com.client

from texttable import Texttable
from serial import *
import serial.tools.list_ports

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtPrintSupport import QPrintDialog, QPrinter, QPrintPreviewDialog
import qc_scale_gui as GUI
import com_config_gui as COM_GUI
from printer import DataToPdfFunc
from printer import TextToPdf


import qc_scale_db_man as DB
import item_name_list as META_DATA


class DbCommitingThread(QtCore.QThread):
	def __init__(self, dbObj, parent=None):
		super(DbCommitingThread, self).__init__(parent)
		self.dbObj = dbObj
		
	def run(self):
		while True:
			time.sleep(5)
			if( self.dbObj.is_changed ):
				self.dbObj.CommitDB()
				
class DataCollectionTheard(QtCore.QThread):
	ser_log_signal = QtCore.pyqtSignal(str)

	def __init__(self, dbObj, parent=None):
		super(DataCollectionTheard, self).__init__(parent)
		self.dbObj = dbObj
		self.ser = Serial()
		self.ser.baudrate = 9600
		self.ser.timeout = 0 # non-blocking readline
		self.ser.port = None
			
	def ScanComPort(self, ser):		
		for port_no, description, address in list(serial.tools.list_ports.comports()):
			if( "USB" in description ):
				return port_no
		
		return None
		
	def OpenComPort(self, com_port, baud_rate, byte_size, parity, stop_bits):
		self.ser.port = com_port
		self.ser.baudrate = baud_rate
		self.ser.bytesize = byte_size
		self.ser.parity = parity
		self.ser.stopbits = stop_bits
		
		try: 
			self.ser.open()
			return True
		except serial.serialutil.SerialException as e: 
			return False
		
	def CloseComPort(self):
		if( self.ser.is_open ): self.ser.close(); return True
		else: return False

	def run(self):	
		while True:
			if( self.ser.is_open ):
				data_line = self.ser.readline()
				data_list = data_line.split()

				if( len(data_list) == 3 ):
					ret = self.dbObj.AddNewTbKetQua(data_list[0].decode("utf8"), 
													data_list[1].decode("utf8"), 
													float(data_list[2].decode("utf8")))

					self.ser_log_signal.emit(datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S] " + 
											 " ".join([str(ele, 'utf-8') for ele in data_list]) + 
											 " => %s" % (ret)))
				time.sleep(0.1)


class ComConfigForm(QtWidgets.QMainWindow, COM_GUI.Ui_ComConfig):
	reload_com_config_signal = QtCore.pyqtSignal()

	def __init__(self, dbObj, parent=None):
		super(ComConfigForm, self).__init__(parent)
		self.setupUi(self)
		
		self.dbObj = dbObj
		
		# binding GUI components
		self.butAddNew.clicked.connect(self.AddNewComConfig)
		self.butDelete.clicked.connect(self.DeleteComConfig)
		
		for config in self.dbObj.SelectAllComConfig():
			self.dbConfigName.addItem("%s : %s : %d : %d : %s : %d" % (config[0], config[2], config[3], config[4], config[5], config[6]))
		
	def ConfigNameChangedEvent(self):
		config_name = self.dbConfigName.currentText()
		com_config = self.dbObj.SelectComConfig(config_name)
		
		if( len(com_config) == 1 ):
			com_config = com_config[0]
			self.lePortNum.setText(com_config[2])
			self.leBaurdrate.setText(str(com_config[3]))
			self.leByteSize.setText(str(com_config[4]))
			self.dbParity.itemText(0 if com_config[5] == "None" else 1 if com_config[5] == "Odd" else "Even")
			self.leStopBit.setText(str(com_config[6]))
		else:
			pass
	
	def AddNewComConfig(self):
		config_name = self.leConfigName.text()
		port_no = self.lePortNum.text()
		baud_rate = int(self.leBaurdrate.text())
		byte_size = int(self.leByteSize.text())
		parity = self.dbParity.currentText()
		stop_bits = int(self.leStopBit.text())
		
		if( self.dbObj.AddNewComConfig(config_name, port_no, baud_rate, byte_size, parity, stop_bits) ):
			self.dbConfigName.addItem("%s : %s : %d : %d : %s : %d" % (config_name, port_no, baud_rate, byte_size, parity, stop_bits))
			self.reload_com_config_signal.emit()
		else: QtWidgets.QMessageBox.warning(self, "Error", "Duplicate COM configuration name !!!")
		
	def DeleteComConfig(self):
		config_name = self.dbConfigName.currentText().split(" : ")[0]
		if( config_name is not "" ):
			if( QtWidgets.QMessageBox.question(self, 'Info', "Are you sure?", QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No) == QtWidgets.QMessageBox.Yes ):
				if( self.dbObj.DeleteComConfig(config_name) ):
					self.dbConfigName.removeItem(self.dbConfigName.currentIndex())
					self.reload_com_config_signal.emit()
				else: QtWidgets.QMessageBox.warning(self, "Error", "Not existed configuration !!!")
		else: QtWidgets.QMessageBox.warning(self, "Error", "Select one configuration !!!")


class MainApp(QtWidgets.QMainWindow, GUI.Ui_MainGui):
	MASTER_PASS = ""

	def __init__(self, dbObj, parent=None):
		super(MainApp, self).__init__(parent)
		self.setupUi(self)
		
		self.dbObj = dbObj
		
		self.commit_thread = DbCommitingThread(self.dbObj)
		self.commit_thread.start()
		self.data_thread = DataCollectionTheard(self.dbObj)
		self.data_thread.start()
		self.data_thread.ser_log_signal.connect(lambda text: self.ptSerialLog.appendPlainText(text))
		self.print_des = ""
		
		# read Master Password
		MainApp.MASTER_PASS = self.dbObj.ReadMasterPass()
		
		# binding GUI components
		self.butLoadTnTieuChuan.clicked.connect(self.LoadTbTieuChuan)
		self.butUpdateTieuChuanRow.clicked.connect(self.UpdateTbTieuChuan)
		self.butQrTyLe.clicked.connect(self.QueryTyLe)
		self.butQrKetQua.clicked.connect(self.QueryKetQua)
		self.butExportDataTab1.clicked.connect(self.ExportTbTieuChuan)
		self.butExportDataTab2.clicked.connect(self.ExportTbKetQua)
		self.butClearLog.clicked.connect(lambda: self.ptSerialLog.setPlainText(""))
		self.butComConnect.clicked.connect(self.ConnectComPort)
		self.butPrintDataTab1.clicked.connect(self.PrintTblTieuChuan)
		self.butPrintDataTab2.clicked.connect(self.PrintTblKetQua)
		self.butPrintLog.clicked.connect(self.PrintLogScreen)
		self.actionPassMan.triggered.connect(self.PassManager)
		
		self.comConfigForm = ComConfigForm(self.dbObj, self)
		self.comConfigForm.reload_com_config_signal.connect(self.ReLoadComConfigForm)
		self.actionComConfig.triggered.connect(lambda: self.comConfigForm.show())
		
		self.dtStart1.setDateTime(QtCore.QDateTime.currentDateTime())
		self.dtEnd1.setDateTime(QtCore.QDateTime.currentDateTime())
		self.dtStart2.setDateTime(QtCore.QDateTime.currentDateTime())
		self.dtEnd2.setDateTime(QtCore.QDateTime.currentDateTime())	
		for item_name in META_DATA.ITEM_NAME_LIST:
			self.dbTenHangTab1.addItem(item_name)
			self.dbTenHangTab2.addItem(item_name)
			
		for config in self.dbObj.SelectAllComConfig():
			self.dbComConfig.addItem("%s : %s : %d : %d : %s : %d" % (config[0], config[2], config[3], config[4], config[5], config[6]))	
		
		# add status bar
		self.statusBar = QtWidgets.QStatusBar()
		self.setStatusBar(self.statusBar)
		
		self.ptSerialLog.setReadOnly(True)
		for _ in range(200):
			self.ptSerialLog.appendPlainText("dao duy tung")
		
		self.setFixedSize(self.size())
		
	def PrintTblTieuChuan(self):
		pdf_file_name = "_temp.pdf"
		data = []
		temp = []
		
		for col in range(self.tbTieuChuan.columnCount()):
			temp.append(self.tbTieuChuan.horizontalHeaderItem(col).text())
		data.append(temp)

		for row in range(self.tbTieuChuan.rowCount()):
			temp = []
			for col in range(self.tbTieuChuan.columnCount()):
				temp.append(self.tbTieuChuan.item(row, col).text())
			data.append(temp)
		
		DataToPdfFunc(data, pdf_file_name, [1,1,1,1,1,2], "Table Tieu Chuan", self.print_des)
		os.system("PDFtoPrinterSelect.exe %s" % (pdf_file_name))
			
	def PrintTblKetQua(self):
		pdf_file_name = "_temp.pdf"
		data = []
		temp = []
		
		for col in range(self.tbKetQua.columnCount()):
			temp.append(self.tbKetQua.horizontalHeaderItem(col).text())
		data.append(temp)
		temp = []
		
		for row in range(self.tbKetQua.rowCount()):
			for col in range(self.tbKetQua.columnCount()):
				temp.append(self.tbKetQua.item(row, col).text())
			data.append(temp)
			temp = []

		if(data[0][0] != "No"):
			DataToPdfFunc(data, pdf_file_name, [1,1,1,1,1,2], "Table Ket Qua", self.print_des)
		else:
			DataToPdfFunc(data, pdf_file_name, [1,1,2,1,1,1], "Table Ket Qua", self.print_des)
		os.system("PDFtoPrinterSelect.exe %s" % (pdf_file_name))
	
	def PrintLogScreen(self):
		pdf_file_name = "_temp.pdf"
		TextToPdf(self.ptSerialLog.toPlainText(), pdf_file_name)
		os.system("PDFtoPrinterSelect.exe %s" % (pdf_file_name))
	
	def ConnectComPort(self):
		if( self.butComConnect.text() == "Connect" ):
			com_config = self.dbComConfig.currentText()
			if( com_config != "" ):
				com_config = com_config.split(" : ")
				com_port = com_config[1]
				baud_rate = int(com_config[2])
				byte_size = int(com_config[3])
				parity = "N" if com_config[4] == "None" else "E" if com_config[4] == "Even" else "O"
				stop_bits = int(com_config[5])
		
				if( self.data_thread.OpenComPort(com_port, baud_rate, byte_size, parity, stop_bits) ):
					self.butComConnect.setText("Disconnect")
				else: QtWidgets.QMessageBox.warning(self, "Error", "could not open port '%s' !!!" % com_port)
			else: QtWidgets.QMessageBox.warning(self, "Error", "Select one configuration !!!")
		else:
			if( self.data_thread.CloseComPort() ):
				self.butComConnect.setText("Connect")
			else: QtWidgets.QMessageBox.warning(self, "Error", "Cannot close COM port !!!")
		
	def ReLoadComConfigForm(self):
		self.dbComConfig.clear()
		for config in self.dbObj.SelectAllComConfig():
			self.dbComConfig.addItem("%s : %s : %d : %d : %s : %d" % (config[0], config[2], config[3], config[4], config[5], config[6]))

	def PassManager(self):
		old_pass, is_ok = QtWidgets.QInputDialog.getText(self, "Input Diaglog", "Enter old Password: ")
		if( is_ok ):
			if( old_pass != "" ):
				if( old_pass == MainApp.MASTER_PASS ):
					new_pass, is_ok = QtWidgets.QInputDialog.getText(self, "Input Diaglog", "Enter new Password: ")
					if( is_ok ):
						if( new_pass != "" ): 
							MainApp.MASTER_PASS = new_pass
							self.dbObj.SetNewPass(new_pass)
							
							QtWidgets.QMessageBox.warning(self, "Info", "Password changed !")
						else: QtWidgets.QMessageBox.warning(self, "Warning", "Password must not be empty")
				else: QtWidgets.QMessageBox.warning(self, "Warning", "Password is not matched")
			else: QtWidgets.QMessageBox.warning(self, "Warning", "Password must not be empty")
				
	def ExportToCsv(self, out_file_name, table_widget):
		headers = []
		for col in range(table_widget.columnCount()):
			headers.append(table_widget.horizontalHeaderItem(col).text())
			
		#with open(out_file_name, "wt") as csv_file:
		with codecs.open(out_file_name, "w", "utf-8") as csv_file:
			csv_file.write("%s\n" % (",".join(headers)))
			
			for row in range (table_widget.rowCount()):
				for col in range(table_widget.columnCount()):
					item = table_widget.item(row, col)
					text = str(item.text()) if( item != None ) else ""
					csv_file.write("%s," % (text))
				csv_file.write("\n")
		
	def ExportTbTieuChuan(self):
		file_name, _ = QtWidgets.QFileDialog.getSaveFileName(self, 'Save File')
		self.ExportToCsv(file_name, self.tbTieuChuan)
	
	def ExportTbKetQua(self):
		file_name, _ = QtWidgets.QFileDialog.getSaveFileName(self, 'Save File')
		self.ExportToCsv(file_name, self.tbKetQua)
	
	def LoadOnTable(self, table_widget, headers, data):
		table_widget.setRowCount(len(data))
		table_widget.setColumnCount(len(headers))
		table_widget.setHorizontalHeaderLabels (headers)
		
		for row_no, row_data in enumerate(data):
			for col_no, col_data in enumerate(row_data):
				table_widget.setItem(row_no, col_no, QtWidgets.QTableWidgetItem(str(col_data)))
				if( str(col_data) == "T" ): table_widget.item(row_no, col_no).setBackground(QtGui.QColor(255,0,0))
				elif( str(col_data) == "D" ): table_widget.item(row_no, col_no).setBackground(QtGui.QColor(255,255,0))
		
	def LoadTbTieuChuan(self):
		rows = self.dbObj.QueryAllTbTieuChuan()				
		self.LoadOnTable(self.tbTieuChuan, ["No", "Ten Hang", "Thap", "Cao"], rows)
				
	def UpdateTbTieuChuan(self):
		item_name = self.dbTenHangTab1.currentText()
		min_val = self.sbMinValTab1.value()	
		max_val = self.sbMaxValTab1.value()
		
		password, is_ok = QtWidgets.QInputDialog.getText(self, "Input Diaglog", "Enter Password: ")
		if( is_ok ):
			if( password == MainApp.MASTER_PASS ):	
				self.dbObj.UpdateTbTieuChuan(item_name, min_val, max_val)
			else: QtWidgets.QMessageBox.warning(self, "Info", "Password is not matched !")
		
	def QueryTyLe(self):
		time_start = self.dtStart1.dateTime().toString("yyyy-MM-dd hh:mm:ss")
		time_end = self.dtEnd1.dateTime().toString("yyyy-MM-dd hh:mm:ss")
		
		#rows = self.dbObj.QuerySummarized('2018-07-01 12:00:00', '2018-07-02 12:00:00')
		rows = self.dbObj.QuerySummarized(time_start, time_end)
		
		self.print_des = "Query TyLe from %s to %s" % (time_start, time_end)
		
		self.LoadOnTable(self.tbKetQua, ["Ten Hang", "So Luong", "Duoi", "OK", "Tren", "Ty Le Ko Dat (%)"], rows)
		
	def QueryKetQua(self):		
		if( self.cbDkThgian.isChecked() or self.cbDkTenHang.isChecked() or self.cbDkKetQua.isChecked() ):
			time_start = self.dtStart2.dateTime().toString("yyyy-MM-dd hh:mm:ss")
			time_end = self.dtEnd2.dateTime().toString("yyyy-MM-dd hh:mm:ss")
			item_name = self.dbTenHangTab2.currentText()
			cond = "= 'O'" if self.dbDkKetQua.currentText() == "OK" else "!= 'O'"
			
			rows = self.dbObj.QueryTbKetQua(time_start if self.cbDkThgian.isChecked()  else None,
											time_end   if self.cbDkThgian.isChecked()  else None,
											item_name  if self.cbDkTenHang.isChecked() else None,
											cond       if self.cbDkKetQua.isChecked()  else None)
											
			self.print_des = "Query KetQua %s%s%s" % ("ThoiGian from %s to %s " % (time_start, time_end) if self.cbDkThgian.isChecked() else "",
													  "TenHang %s" % (item_name) if self.cbDkTenHang.isChecked() else "",
													  "KetQua %s" % cond if self.cbDkKetQua.isChecked() else "")
			
			self.LoadOnTable(self.tbKetQua, ["No", "STT", "Thoi Gian", "Ten Hang", "Trong Luong", "Ket Qua"], rows)
		else: QtWidgets.QMessageBox.warning(self, "Warning", "Select at least 1 condition")


if __name__ == "__main__":
	dbObj = DB.QcScaleDataMan("qc_scale_db.sqlite")
	dbObj.InitDB()
	
	# start GUI
	app = QtWidgets.QApplication(sys.argv)
	form = MainApp(dbObj)
	form.show()
	app.exec_()
	
	# last commit before closing
	dbObj.CommitDB()
	dbObj.DeInitDB()
	
	sys.exit()