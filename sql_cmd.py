# SQL commands defination
SQL_CMD_SET_TB_COM_CONFIG = {
	"CREATE_TB": '''CREATE TABLE tblComConfig (
					ConfigName TEXT PRIMARY KEY NOT NULL, 
					ThoiGian timestamp NOT NULL, 
					PortNo TEXT NOT NULL,
					Baudrate INTEGER NOT NULL,
					ByteSize INTEGER NOT NULL,
					Parity TEXT NOT NULL,
					StopBits INTEGER NOT NULL,
					LastUsed INTEGER NOT NULL)''',
	"ADD_NEW_CONFIG": '''INSERT INTO tblComConfig 
							(ConfigName, ThoiGian, PortNo, Baudrate, ByteSize, Parity, StopBits, LastUsed) 
							VALUES
							('{ConfigName}', '{ThoiGian}', '{PortNo}', {Baudrate}, {ByteSize}, '{Parity}', {StopBits}, {LastUsed})''',
	"SELECT_CONFIG": "SELECT * FROM tblComConfig WHERE ConfigName = '{ConfigName}'",
	"DELETE_CONFIG": "DELETE FROM tblComConfig WHERE ConfigName = '{ConfigName}'",
	"SELECT_ALL_CONFIG": "SELECT * FROM tblComConfig"
}
SQL_CMD_SET_TB_PASSWORD = {
	"CREATE_TB": '''CREATE TABLE tblPassword (
					No INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, 
					ThoiGian timestamp NOT NULL, 
					Password TEXT NOT NULL)''',
	"SELECT_LAST_PASS": "SELECT * FROM tblPassword ORDER BY ThoiGian DESC LIMIT 1",
	"ADD_NEW_PASS": "INSERT INTO tblPassword (ThoiGian, Password) VALUES ('{ThoiGian}', '{Password}')"
}
SQL_CMD_SET_TB_TIEUCHUAN = {
	"CREATE_TB" 	: '''CREATE TABLE tblTieuChuan (
						No INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, 
						TenHang TEXT NOT NULL, 
						Thap INTEGER NOT NULL, 
						Cao INTEGER NOT NULL)''',
	"ADD_NEW_REC" 	: "INSERT INTO tblTieuChuan (TenHang, Thap, Cao) VALUES ('{TenHang}',{Thap},{Cao})",
	"UPDATE_RANGE" 	: "UPDATE tblTieuChuan SET Thap = {Thap}, Cao = {Cao} WHERE TenHang = '{TenHang}'",
	"SELECT_RANGE" 	: "SELECT Thap, Cao FROM tblTieuChuan WHERE TenHang = '{TenHang}'",
	"SELECT_ALL"	: "SELECT * FROM tblTieuChuan"
}
SQL_CMD_SET_TB_KETQUA = {
	"CREATE_TB" 	: '''CREATE TABLE tblKetQua (
						No INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, 
						STT TEXT NOT NULL, 
						NgayThangThoiGian timestamp NOT NULL, 
						TenHang TEXT NOT NULL, 
						TrongLuong INTEGER NOT NULL, 
						KetQua TEXT NOT NULL)''',
	"ADD_NEW_REC" 	: "INSERT INTO tblKetQua (STT, NgayThangThoiGian, TenHang, TrongLuong, KetQua) VALUES ('{STT}', '{NgayThangThoiGian}', '{TenHang}', {TrongLuong}, '{KetQua}')",
	"UPDATE_KETQUA" : '''UPDATE tblKetQua SET KetQua = 
						 CASE 
							WHEN TrongLuong < '{Min}' 
								THEN 'D' 
								ELSE 
									CASE 
										WHEN TrongLuong > '{Max}' 
											THEN 'T' 
											ELSE 'O' 
									END 
						 END 
						 WHERE TenHang = '{TenHang}' ''',
	"QUERY_KET_QUA" : "SELECT * FROM tblKetQua WHERE {WHERE_CLAUSE}",
	"QUERY_TY_LE"	: '''SELECT 
					     	TenHang, 
					     	count(TenHang) AS 'SoLuong',
					     	count(CASE WHEN KetQua = 'D' THEN 1 ELSE null END) AS 'Duoi',
					     	count(CASE WHEN KetQua = 'O' THEN 1 ELSE null END) AS 'OK',
					     	count(CASE WHEN KetQua = 'T' THEN 1 ELSE null END) AS 'Tren',
					     	(count(CASE WHEN KetQua = 'D' THEN 1 ELSE null END) + count(CASE WHEN KetQua = 'T' THEN 1 ELSE null END)) * 1.0 / 
					     	(count(CASE WHEN KetQua = 'O' THEN 1 ELSE null END) + count(CASE WHEN KetQua = 'D' THEN 1 ELSE null END) + count(CASE WHEN KetQua = 'T' THEN 1 ELSE null END)) * 100 AS 'TyLeKoDat'
					     	FROM tblKetQua
						 WHERE NgayThangThoiGian BETWEEN '{DateTimeStart}' AND '{DateTimeEnd}'
						 GROUP BY TenHang'''
}