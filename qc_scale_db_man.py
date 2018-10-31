import os, sys
import datetime, time
import sqlite3
import random
import qc_scale_logger as LOGGER

import sql_cmd as CMD
import item_name_list as META_DATA

class QcScaleDataMan():						
	def __init__(self, sqlite_file_name):
		self.conn = sqlite3.connect(sqlite_file_name, detect_types=sqlite3.PARSE_DECLTYPES, check_same_thread=False)
		self.curs = self.conn.cursor()
		self.is_changed = False
		
	def SqlExecute(self, sql_cmd):
		sql_cmd = sql_cmd.replace('\t', '').replace('\r', '').replace('\n', '')
		
		start_time = datetime.datetime.now()
		self.curs.execute(sql_cmd)
		self.is_changed = True
		last_elapsed_time = datetime.datetime.now() - start_time
		
		LOGGER.logger.debug("SQL cmd: %s >>> Exe Time = %s" % (sql_cmd, last_elapsed_time))
		
	def InitTbTieuChuan(self):		
		# Add pre-defined records
		for item_name in META_DATA.ITEM_NAME_LIST:
			#self.SqlExecute(CMD.SQL_CMD_SET_TB_TIEUCHUAN["ADD_NEW_REC"].format(TenHang=code + "-" + thickness, Thap=0, Cao=999.99))
			self.SqlExecute(CMD.SQL_CMD_SET_TB_TIEUCHUAN["ADD_NEW_REC"].format(TenHang=item_name, Thap=44.99, Cao=50.99))
		
		# Add unused records
		for _ in range(250 - (len(META_DATA.ITEM_NAME_LIST))):
			self.SqlExecute(CMD.SQL_CMD_SET_TB_TIEUCHUAN["ADD_NEW_REC"].format(TenHang="UNDEF  ", Thap=0, Cao=999.99))
	
	def CommitDB(self):
		start_time = datetime.datetime.now()
		self.conn.commit()
		self.is_changed = False
		last_elapsed_time = datetime.datetime.now() - start_time
		
		LOGGER.logger.info("DB Commited >>> Exe Time = %s" % (last_elapsed_time))
	
	def DeInitDB(self):
		self.conn.close()
		LOGGER.logger.info("Database has been closed")
	
	def InitDB(self):
		# tblTieuChuan
		try: 
			self.SqlExecute(CMD.SQL_CMD_SET_TB_TIEUCHUAN["CREATE_TB"])
			self.InitTbTieuChuan()
		except sqlite3.OperationalError as e:
			LOGGER.logger.warn("tblTieuChuan has initialized before")
		
		# tblKetQua
		try: 
			self.SqlExecute(CMD.SQL_CMD_SET_TB_KETQUA["CREATE_TB"])
		except sqlite3.OperationalError as e:
			LOGGER.logger.warn("tblKetQua has initialized before")
			
		# tblPassword
		try: 
			self.SqlExecute(CMD.SQL_CMD_SET_TB_PASSWORD["CREATE_TB"])
			self.SqlExecute(CMD.SQL_CMD_SET_TB_PASSWORD["ADD_NEW_PASS"].format(ThoiGian=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), Password="27052013"))
		except sqlite3.OperationalError as e:
			LOGGER.logger.warn("tblPassword has initialized before")
			
		# tblComConfig
		try: 
			self.SqlExecute(CMD.SQL_CMD_SET_TB_COM_CONFIG["CREATE_TB"])
		except sqlite3.OperationalError as e:
			LOGGER.logger.warn("tblComConfig has initialized before")
		
	def UpdateTbTieuChuan(self, item_name, min_val, max_val):
		# refer weight range from tblTieuChuan
		self.SqlExecute(CMD.SQL_CMD_SET_TB_TIEUCHUAN["SELECT_RANGE"].format(TenHang=item_name))
		selected_row = self.curs.fetchall()
		
		if( len(selected_row) == 1 ):
			# only udpate when new range is applied
			if( min_val != selected_row[0][0] or max_val != selected_row[0][1]):
				self.SqlExecute(CMD.SQL_CMD_SET_TB_TIEUCHUAN["UPDATE_RANGE"].format(TenHang=item_name, Thap=min_val, Cao=max_val))
				
				# re-check KetQua with new range			
				self.SqlExecute(CMD.SQL_CMD_SET_TB_KETQUA["UPDATE_KETQUA"].format(Min=min_val,
																				  Max=max_val,
																				  TenHang=item_name))
		else:
			LOGGER.logger.error("Unexpected data queried from tblTieuChuan")
			
	def AddNewTbKetQua(self, stt, item_name, weight):
		ket_qua = ""
	
		# refer weight range from tblTieuChuan
		self.SqlExecute(CMD.SQL_CMD_SET_TB_TIEUCHUAN["SELECT_RANGE"].format(TenHang=item_name))
		
		selected_row = self.curs.fetchall()
		if( len(selected_row) == 1 ): 
			if( weight < selected_row[0][0] ): 		ket_qua += "D"
			elif( weight > selected_row[0][1] ): 	ket_qua += "T"
			else:									ket_qua += "O"
		else: print("ko vao")
		
		self.SqlExecute(CMD.SQL_CMD_SET_TB_KETQUA["ADD_NEW_REC"].format(STT=stt,
																		NgayThangThoiGian=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
																		#NgayThangThoiGian=(datetime.datetime.now() - datetime.timedelta(random.uniform(0,10))).strftime("%Y-%m-%d %H:%M:%S"),
																		TenHang=item_name,
																		TrongLuong=weight,
																		KetQua=ket_qua))
		return ket_qua																

	def QueryTbKetQua(self, time_start, time_end, item_name, cond):
		time_clause = item_clause = cond_clause = "1"
		if( time_start != None and time_end != None ):
			time_clause = "NgayThangThoiGian BETWEEN '%s' AND '%s'" % (time_start, time_end)
		if( item_name != None ):
			item_clause = "TenHang = '%s'" % (item_name)
		if( cond != None ):
			cond_clause = "KetQua %s" % (cond)
		where_clause = " AND ".join([time_clause, item_clause, cond_clause])
		
		self.SqlExecute(CMD.SQL_CMD_SET_TB_KETQUA["QUERY_KET_QUA"].format(WHERE_CLAUSE=where_clause))
		selected_row = self.curs.fetchall()
		return selected_row
	
	def QuerySummarized(self, time_start, time_end):
		self.SqlExecute(CMD.SQL_CMD_SET_TB_KETQUA["QUERY_TY_LE"].format(DateTimeStart=time_start, DateTimeEnd=time_end))
		selected_row = self.curs.fetchall()
		return selected_row
			
	def QueryAllTbTieuChuan(self):
		self.SqlExecute(CMD.SQL_CMD_SET_TB_TIEUCHUAN["SELECT_ALL"])
		selected_row = self.curs.fetchall()
		return selected_row
		
	def ReadMasterPass(self):
		self.SqlExecute(CMD.SQL_CMD_SET_TB_PASSWORD["SELECT_LAST_PASS"])
		selected_row = self.curs.fetchall()
		if( len(selected_row) == 1 ):
			return selected_row[0][2]
			
	def SetNewPass(self, new_pass):
		self.SqlExecute(CMD.SQL_CMD_SET_TB_PASSWORD["ADD_NEW_PASS"].format(ThoiGian=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
																		   Password=new_pass))
																		   
	def SelectComConfig(self, config_name):
		self.SqlExecute(CMD.SQL_CMD_SET_TB_COM_CONFIG["SELECT_CONFIG"].format(ConfigName=config_name))
		selected_row = self.curs.fetchall()
		
		return selected_row
		
	def SelectAllComConfig(self):
		self.SqlExecute(CMD.SQL_CMD_SET_TB_COM_CONFIG["SELECT_ALL_CONFIG"])
		selected_row = self.curs.fetchall()
		
		return selected_row
		
	def AddNewComConfig(self, config_name, port_no, baud_rate, byte_size, parity, stop_bits):
		try: 
			self.SqlExecute(CMD.SQL_CMD_SET_TB_COM_CONFIG["ADD_NEW_CONFIG"].format(ConfigName=config_name,
																				   ThoiGian=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
																				   PortNo=port_no,
																				   Baudrate=baud_rate,
																				   ByteSize=byte_size,
																				   Parity=parity,
																				   StopBits=stop_bits,
																				   LastUsed=0))
			return True
		except sqlite3.IntegrityError as e:
			return False
			
	def DeleteComConfig(self, config_name):
		try: 
			self.SqlExecute(CMD.SQL_CMD_SET_TB_COM_CONFIG["DELETE_CONFIG"].format(ConfigName=config_name))
			return True
		except sqlite3.IntegrityError as e:
			return False
	
def Test(db):
	item_codes = ["L0", "Q ", "T ", "X ", "Z ", "W ", "Y ", "C "]
	item_thicknesses = [" 1.5", " 1.8", " 2.0", " 2.5", " 2.8", " 3.0", " 4.0", 
						" 4.5", " 5.0", " 5.5", " 6.0", " 8.0", " 9.0", " 9.5", 
						"10.0", "12.0", "  15", "  18", "  20", "  25", "  30"]
	ten_hang_list = []
	
	for code in item_codes:
		for thickness in item_thicknesses:
			ten_hang_list.append(code + "-" + thickness)

	for idx in range(20000):
		db.AddNewTbKetQua(str(idx), random.choice(ten_hang_list), random.randint(40,55))
		
if __name__ == '__main__':	
	dbObj = QcScaleDataMan("qc_scale_db.sqlite")
	dbObj.InitDB()
	
	Test(dbObj)
	#dbObj.UpdateTbTieuChuan("T - 8.0", 999.12, 999.99)
	print(dbObj.QuerySummarized('2018-07-01 09:30:00', '2018-07-04 09:38:00'))
	#dbObj.QueryTbKetQua('2018-07-01 09:30:00', '2018-07-04 09:38:00', 'T - 5.0', "!= 'O'")
	
	dbObj.CommitDB()
	dbObj.DeInitDB()