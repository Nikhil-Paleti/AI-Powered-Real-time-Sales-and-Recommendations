from pyspark.sql.session import SparkSession
from pyspark.sql.functions import *
from datetime import datetime, date
from pyspark.sql import Row
from pymongo import MongoClient
import pandas as pd

client = MongoClient('mongodb+srv://admin:admin@cluster0.75ml3wq.mongodb.net/?retryWrites=true&w=majority')
#client = MongoClient('localhost', 27017)

db1 = client.AISupermarket
collection_main = db1.Invoice
curr_invoice = int(collection_main.find_one(sort=[("InvoiceNo", -1)])['InvoiceNo']) + 1


def get_invoice(purch_item_list):
    global item_list
    if purch_item_list == None:
        return None
    else:
        quantity = {}
        subtotal = {}
        for item in purch_item_list:
            if item in item_list.keys():
                quantity[item] = 0
                subtotal[item] = 0
        total = 0
        for item in purch_item_list:
            if item in item_list.keys():
                quantity[item] += 1 
                subtotal[item] += item_list[item]
                total += item_list[item]
                #total += total*0.05

    return quantity, subtotal, total


spark = SparkSession.builder.appName("AISupermarket").master("local[*]") \
    .config("spark.mongodb.input.uri", ("mongodb+srv://admin:admin@cluster0.75ml3wq.mongodb.net/AISupermarket.Invoice")) \
    .config("spark.mongodb.output.uri", ("mongodb+srv://admin:admin@cluster0.75ml3wq.mongodb.net/AISupermarket.Invoice")) \
    .getOrCreate()

spark.sparkContext.setLogLevel("ERROR")
df = spark.readStream.format("kafka").option("kafka.bootstrap.servers", "localhost:9092").option("subscribe", "invoice_kaf").load()



# df1 = df.selectExpr("cast(value as string) as kafka_output")\
#     .withColumn("kafka_output_new", regexp_replace("kafka_output","\\\\","")).drop("kafka_output")

df1 = df.selectExpr("cast(value as string) as kafka_output")

df1.writeStream.format("console").option("truncate","false").outputMode("Append").start()


item_list = {
        #Aisle 1
        "tv" : 29999.99, "laptop":56324.99 , "mouse": 1349.99, "remote": 949.99, "keyboard": 1499.99, "cellphone": 19999.99,
        #Aisle 2
        "microwave": 8399.99, "oven":6534.99, "toaster":1999.99, "sink":1299.99, "refrigerator":16299.99, "blender":5999.99,
        #Aisle 3
        "book": 249.99, "clock": 699.99, "vase": 2249.99, "scissors": 149.99, "teddybear":349.99, "hairdrier":1699.99, "toothbrush": 19.99,
        #Aisle 4
        "chair": 2999.99, "couch":9999.99, "pottedplant":249.99, "bed":14999.99, "mirror":99.99, "diningtable":12999.99, "window":4999.99, "desk":3549.99, "door":889.99,
        #Aisle 5
        "banana":3, "apple":2, "sandwich":249.99, "orange":20, "broccoli":30, "carrot":5, "pizza":449.99, "donut":49.99, "cake":499.99,
        #Aisle 6
        "bottle":19.99, "plate":399.99, "cup":249.99, "fork":99.99, "knife":149.99, "spoon":99.99, "bowl":299.99,
        #Aisle 7
        "hat": 199.99, "backpack" : 999.99, "umbrella" : 299.99, "shoe": 1249.99, "eye_glasses" : 399.99, "handbag": 349.99, "suitcase": 1999.99
    }

aile_names = ["Electronics", "Kitchen", "Stationary", "Furniture", "Grocery", "Utensils", "Clothing"]

item_ailes = {}

ailes = {
    "a1" : ["tv","laptop","mouse","remote","keyboard","cellphone"],
    "a2" : ["microwave", "oven", "toaster", "sink", "refrigerator", "blender",],
    "a3" : ["book", "clock", "vase", "scissors", "teddybear", "hairdrier", "toothbrush"],
    "a4" : ["chair", "couch", "pottedplant", "bed", "mirror", "diningtable", "window", "desk", "door"],
    "a5" : ["banana", "apple", "sandwich", "orange", "broccoli", "carrot", "pizza", "donut", "cake"],
    "a6" : ["bottle", "plate", "cup", "fork", "knife", "spoon", "bowl"],
    "a7" : ["hat", "backpack", "umbrella", "shoe", "eyeglasses", "handbag", "suitcase"],
}

for i in range(1, len(ailes)+1):
    arr = ailes[f"a{i}"]
    for item in arr:
        item_ailes[item] = i


def mongoInsert(dataframe, epoch_id):
    global curr_invoice,item_ailes
    try:
        if dataframe.count() > 0:
            str = dataframe.collect()[0].__getitem__("kafka_output").replace("\"", "").split()
            item_list = str[3].split(",")
            quantity,subtotal,total = get_invoice(item_list)
            aile_no = []
            for i in item_list:
                aile_no.append(item_ailes[i])
            cur_DT = datetime.now()
            #curr_invoice = 0
            dataframe = spark.createDataFrame([
            Row(
                InvoiceNo = curr_invoice, 
                FirstName=str[0], 
                LastName=str[1],
                PhoneNumber = str[2] ,
                Date = cur_DT.strftime("%d/%m/%Y"), 
                Time = cur_DT.strftime("%H:%M:%S"), 
                DayOfWeek = cur_DT.strftime("%A"),
                Items=quantity,
                Aisle_visited = aile_no,
                SubTotal=subtotal,
                Total=total)
            ])

    #         database = database.append(
    #     {
    #         "InvoiceNo" : count,
    #         "FirstName" : cust.split(" ")[0],
    #         "LastName" : cust.split(" ")[1],
    #         "PhoneNumber" : ph_no,
    #         #"CustID" : customerDatabase.iloc[random_cust].CustID,
    #         "Date" : dates.iloc[i].strftime("%d/%m/%Y"),
    #         "Time" : dates.iloc[i].strftime("%H:%M:%S"),
    #         "DayOfWeek" : dates.iloc[i].strftime("%A"),
    #         #"Items" : ",".join(items),
    #         "Items" : quantity,
    #         "Aisle_visited" : [aile_names[i-1] for i in aile_no],
    #         "SubTotal" : subtotal,
    #         "Total" : total
    #     }, 
    #     ignore_index=True
    # )
            curr_invoice += 1
            print("Inserting into MongoDB")
            dataframe.show()
            dataframe.write.format("mongo").mode("append").save()
    except Exception as e:
        print(e)
       

df1.writeStream.foreachBatch(mongoInsert).start().awaitTermination()
