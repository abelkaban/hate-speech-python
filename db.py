import mysql.connector
import json
import math

from process import Process

class DB:
    tableName   = 'train_result'
    def __init__(self):
        mydb = mysql.connector.connect(
            host    ="localhost",
            user    ="root",
            password="B0yd@nnoah",
            database="hatespeech"
        )

        mycursor = mydb.cursor()

        self.mydb       = mydb
        self.mycursor   = mycursor

    def prepareTable(self):
        # try:
        self.mycursor.execute("SELECT * FROM information_schema.tables WHERE table_name = '"+self.tableName+"'")

        total   = len(self.mycursor.fetchall())

        if total < 1:
            self.mycursor.execute("CREATE TABLE `"+self.tableName+"` (`type` varchar(255) NOT NULL, `term` varchar(255) NOT NULL,`total_negatif` int DEFAULT 0,`total_positif` int DEFAULT 0,`total_term` int DEFAULT 0, `n11` int DEFAULT 0, `n01` int DEFAULT 0, `n10` int DEFAULT 0, `n00` int DEFAULT 0, `n1_` int DEFAULT 0, `n1` int DEFAULT 0, `n0_` int DEFAULT 0, `n0` int DEFAULT 0, `mi` double DEFAULT 0, PRIMARY KEY (`term`, `type`))")
            self.populateData()
        else:
            print('none')
            self.populateData()
        # except Exception as e:
        #     print(e)

    def populateData(self):
        process = Process()
        # try:
        self.mycursor.execute('TRUNCATE TABLE ' + self.tableName)
        totalNeg    = 0
        totalPos    = 0

        mi  = process.composeData()

        for row in mi:
            totalNeg += mi[row]['negatif']['total']
            totalPos += mi[row]['positif']['total']
        

        n   = totalNeg+totalPos
        for row in mi:
            query       = "INSERT INTO "+self.tableName+" (type, term, total_negatif, total_positif, total_term, n11, n01, n10, n00, n1, n1_, n0, n0_, mi) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"

            n11     = mi[row]['positif']['total']
            n01     = (totalPos - mi[row]['positif']['total'])
            n10     = mi[row]['negatif']['total']
            n00     = (totalNeg - mi[row]['negatif']['total'])
            n1_     = n10+n11
            n1      = n01+n11
            n0_     = n01+n00
            n0      = n10+n00

            r       = (n11/n)*(process.cleanLog2((n*n11), (n1_*n1)))
            s       = (n01/n)*(process.cleanLog2((n*n01), (n0_*n1)))
            t       = (n10/n)*(process.cleanLog2((n*n10), (n1_*n0)))
            u       = (n00/n)*(process.cleanLog2((n*n00), (n0_*n0)))
            finalMI = r+s+t+u

            valuesPos   = ('positif',row, mi[row]['negatif']['total'], mi[row]['positif']['total'], mi[row]['total'], n11, n01, n10, n00, n1, n1_, n0, n0_, finalMI)
            self.mycursor.execute(query, valuesPos)

            n11     = mi[row]['negatif']['total']
            n01     = (totalNeg - mi[row]['negatif']['total'])
            n10     = mi[row]['positif']['total']
            n00     = (totalPos - mi[row]['positif']['total'])
            n1_     = n10+n11
            n1      = n01+n11
            n0_     = n01+n00
            n0      = n10+n00

            r       = (n11/n)*(process.cleanLog2((n*n11), (n1_*n1)))
            s       = (n01/n)*(process.cleanLog2((n*n01), (n0_*n1)))
            t       = (n10/n)*(process.cleanLog2((n*n10), (n1_*n0)))
            u       = (n00/n)*(process.cleanLog2((n*n00), (n0_*n0)))
            finalMI = r+s+t+u

            valuesNeg   = ('negatif',row, mi[row]['negatif']['total'], mi[row]['positif']['total'], mi[row]['total'], n11, n01, n10, n00, n1, n1_, n0, n0_, finalMI)
            self.mycursor.execute(query, valuesNeg)

            self.mydb.commit()

        #     print('term "'+row+'" inserted')

    def refactorTable(self):
        self.mycursor.execute("DROP TABLE IF EXISTS `"+self.tableName+"`")
        self.prepareTable()

    def reorderTableData(self):
        self.mycursor.execute("SELECT count(term) FROM "+self.tableName)

        result  = self.mycursor.fetchone()
        total   = result[0]

        per75   = math.ceil((75/100) * total)

        self.mycursor.execute("SELECT * FROM "+self.tableName+" ORDER BY mutual_information DESC LIMIT "+str(per75))

        fresh   = self.mycursor.fetchall()

        self.mycursor.execute('TRUNCATE TABLE '+self.tableName)

        for row in fresh:
            query   = "INSERT INTO " + self.tableName + " (term, total, negatif, positif, mutual_information) VALUES (%s, %s, %s, %s, %s)"
            values  = (row[0], row[1], row[2], row[3], row[4])
            self.mycursor.execute(query, values)
            self.mydb.commit()

        print('table data re-ordered successfully to 75%')

    def validateWords(self, value, name):
        process = Process()
        terms   = process.cleanComment(value)
        pPos    = []
        pNeg    = []

        tPos = 0
        tNeg = 0

        for word in terms:
            self.mycursor.execute("SELECT * FROM " + self.tableName + " WHERE term='" + word + "'")
            # rows.append()
            res = self.mycursor.fetchone()

            if res == None:
                pPos.append(0)
                pNeg.append(0)

                tPos += 0
                tNeg += 0
            else:
                vPos = res[3] / (res[3] + res[2]) if res[3] > 0 else 0
                vNeg = res[2] / (res[3] + res[2]) if res[2] > 0 else 0
                pPos.append(vPos)
                pNeg.append(vNeg)

                tPos += vPos
                tNeg += vNeg

            # print("Tidak ada" if res == None else res)

        tPos = math.exp(tPos)
        tNeg = math.exp(tNeg)

        sum = tPos + tNeg

        tPos = tPos / sum
        tNeg = tNeg / sum

        result = 'Positif' if tPos > tNeg else 'Negatif'

        return {
            'nama'      : name,
            'komentar'  : value,
            'positif'   : tPos,
            'negatif'   : tNeg,
            'hasil'     : result
        }
