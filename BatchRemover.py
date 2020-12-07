import json
import csv
from appJar import gui
#import pylightxl as xl
import time

def convertJSONToCSV():
    #Process JSON file
    print("\n>Converting JSON file to CSV")
    with open(a.getEntry("JSON")) as json_file:
        data = json.load(json_file)
    data_file = open("ACE_Manifest_(CSV).csv", "w", newline="")
    csv_writer = csv.writer(data_file)

    for l in data: #for line in data:
        #try:
        ''' 2020-11-26 Problem with Province Of Loading. Hardcoding for the time being
        #DHL Manifests don't have Province of Loading T.T
        try:
            _province_of_loading = l["provinceOfLoading"],
        except:
            _province_of_loading = "ON"
        '''
        try:
            _consignee_province = l["consignee"]["address"]["stateProvince"]
            _consignee_postal_code = l["consignee"]["address"]["postalCode"]
        except:
            _consignee_province = ""
        try:
            _shipper_name = l["shipper"]["name"]
            _shipper_address = l["shipper"]["address"]["addressLine"]
            _shipper_country = l["shipper"]["address"]["country"]
            _shipper_city = l["shipper"]["address"]["city"]
            _shipper_province = l["shipper"]["address"]["stateProvince"]
            _shipper_postal_code = l["shipper"]["address"]["postalCode"]
        except:
            _shipper_name = "Stalco Inc."
            _shipper_address = "401 Clayson Road"
            _shipper_country =  "CA"
            _shipper_city = "Toronto"
            _shipper_province = "ON"
            _shipper_postal_code = "M9M2H4"
        
        head = ( #Doing it manually for now. This format doesn't change often
            l["ORDERID"],
            l["BATCHID"],
            l["data"],
            l["type"],
            l["shipmentControlNumber"],
            # Defaults for when ACE is missing entries
            #_province_of_loading,
            "ON", #2020-11-26 hardcoding Temporarily
            _shipper_name,
            _shipper_address,
            _shipper_country,
            _shipper_city,
            _shipper_province,
            _shipper_postal_code,
            l["consignee"]["name"],
            l["consignee"]["address"]["addressLine"],
            l["consignee"]["address"]["country"],
            l["consignee"]["address"]["city"],
            _consignee_province,
            _consignee_postal_code
        )
        for i, commodity in enumerate(l["commodities"]): #for commodity in line["commodities"]
            body = (
                l["commodities"][i]["description"],
                l["commodities"][i]["quantity"],
                l["commodities"][i]["packagingUnit"],
                l["commodities"][i]["weight"],
                l["commodities"][i]["weightUnit"]
            )
            #if l["commodities"][i]["value"] != "":
            if "value" in l["commodities"][i].keys():
                body = body + (l["commodities"][i]["value"],)
            if "countryOfOrigin" in l["commodities"][i]:
                body = body + (l["commodities"][i]["countryOfOrigin"],)
            row = head + body
            csv_writer.writerow(row)
        #except:
            #print("Error on order ID {}".format(l["ORDERID"],))
    data_file.close()
    print("Finished converting JSON")
    print("Outputting to \"ACE_Manifest_(CSV).csv\"")

def convertCSVToJSON():
    print("\n>Converting CSV file to JSON")
    with open(a.getEntry("CSV")) as csv_file:
    #with open("C:\\Users\\Alex\\Desktop\\Alex's Workspace\\BatchRemover\\output.csv") as csv_file:
        csv_reader = csv.reader(csv_file, delimiter = ',')
        csv_data = []
        for row in csv_reader:
            csv_data.append(row)
            
        #Makes a list of consignees to add to JSON
        consignees = []
        for row in csv_data:
            if row[4] not in consignees:
                consignees.append(row[4])

        #For each consignee, add each entry to JSON
        out_json = []
        for consignee in consignees:
            #print("Building {}".format(consignee))
            entry = {}
            for row in csv_data:
                if consignee == row[4]:
                    #print("Match found for {}".format(consignee))
                    entry = {
                        "ORDERID": row[0],
                        "BATCHID": row[1],
                        "data": row[2],
                        "type": row[3],
                        "shipmentControlNumber": row[4],
                        "provinceOfLoading": row[5],
                        "shipper": {
                            "name": row[6],
                            "address": {
                                "addressLine": row[7],
                                "country": row[8],
                                "city": row[9],
                                "stateProvince": row[10],
                                "postalCode": row[11].zfill(5)
                            }
                        },
                        "consignee": {
                            "name": row[12],
                            "address": {
                                "addressLine": row[13],
                                "country": row[14],
                                "city": row[15],
                                "stateProvince": row[16],
                                "postalCode": row[17]
                            }
                        },
                        "commodities": []
                    }

            for row in csv_data: #Searches for commodities that match consignee
                if consignee == row[4]:
                    commodity = {}
                    if len(row) == 25: #If the entry has value and countryOfOrigin
                        commodity = {
                            "description": row[18],
                            "quantity": float(row[19]),
                            "packagingUnit": row[20],
                            "weight": int(row[21]),
                            "weightUnit": row[22],
                            "value": row[23],
                            "countryOfOrigin": row[24]
                        }
                    elif len(row) == 24: #If it has only value
                        commodity = {
                            "description": row[18],
                            "quantity": float(row[19]),
                            "packagingUnit": row[20],
                            "weight": int(row[21]),
                            "weightUnit": row[22],
                            "value": row[23],
                        }
                    else:
                        commodity = {
                            "description": row[18],
                            "quantity": float(row[19]),
                            "packagingUnit": row[20],
                            "weight": int(row[21]),
                            "weightUnit": row[22]
                        }
                    entry["commodities"].append(commodity)
            out_json.append(entry)
        with open("ACE_Manifest_(JSON).json", "w") as json_file:
            json.dump(out_json, json_file, indent=4)
        print(">Done converting CSV to JSON")
        print("Outputting to \"ACE_Manifest_(JSON).json\"")
    
def removeOrders():
    print("\n>Splitting ACE")
    orders = a.getTextArea("ordersTextArea")
    orders = orders.replace("\n", ",")
    orders_list = orders.split(",")
    
    with open(a.getEntry("ACE")) as json_file:
        json_data = json.load(json_file)
        data = json_data.copy()

    #Create blacklist    
    blacklist = []
    with open("blacklist.txt", "r") as blacklist_file:
        lines = blacklist_file.readlines()
    for line in lines:
        if line[0] != "#": #Comments
            blacklist.append(line.replace("\n", ""))

    #Split out orders
    split_orders = []
    for entry in json_data:
        
        #Match blacklisted cmmodities
        for commodity in entry["commodities"]:
            for blacklist_item in blacklist:
                if blacklist_item in commodity["description"]:
                    data.remove(entry)
                    print("Blacklisted item found: {} for {}".format(commodity["description"], entry["consignee"]["name"]))

        #Match Transaction/Batch ID
        for order in orders_list:
            if entry["ORDERID"] == order or entry["BATCHID"] == order :
                split_orders.append(entry)
                data.remove(entry)
                print("Removed order {} for {}".format(order, entry["consignee"]["name"]))
    #Output
    with open("ACE_Manifest_(1).json", "w") as json_file:
            json.dump(data, json_file, indent = 4)
    with open("ACE_Manifest_(2).json", "w") as bad_orders_file:
            json.dump(split_orders, bad_orders_file, indent = 4)
    print("Finished splitting ACE")
    print("Outputting original ACE to \"ACE_Manifest_(1).json\"")
    print("Outputting split entries to \"ACE_Manifest_(2).json\"")

def jsonBeautifier():
    print("\n>Formatting JSON")
    json_file_name = a.getEntry("Ugly JSON")
    with open(json_file_name, "r") as json_file:
        json_data = json.load(json_file)
    out_file_name = "ACE_Manifest_(Cleaned).json"
    with open(out_file_name, "w") as json_file:
        json.dump(json_data, json_file, indent = 4)
    print("Done formatting JSON")
    print("Outputting to \"ACE_Manifest_(Cleaned).json\"")

def combineJSON():
    print(">Combining JSONs")
    out_data = []
    with open(a.getEntry("JSON 1"), "r") as json_file_1:
        json_data_1 = json.load(json_file_1)
    with open(a.getEntry("JSON 2"), "r") as json_file_2:
        json_data_2 = json.load(json_file_2)
    for line in json_data_1:
        out_data.append(line)
    for line in json_data_2:
        out_data.append(line)
    with open("ACE_Manifest_(Combined).json", "w") as json_file:
        json.dump(out_data, json_file, indent = 4)
    print("Done combining JSONs")
    print("Outputting to \"ACE_Manifest_(Combined).json\"")

### Main

a = gui()
a.startLabelFrame("Manual Editting")
a.addLabelFileEntry("JSON")
a.addButton("Convert to CSV", convertJSONToCSV)
a.addLabelFileEntry("CSV")
a.addButton("Convert to JSON", convertCSVToJSON)
a.stopLabelFrame()

a.startLabelFrame("Automatic Editting")
a.addLabelFileEntry("ACE")
a.addLabel("Batches/Transactions")
a.addTextArea("ordersTextArea")
a.addButton("Remove/Split", removeOrders)
a.stopLabelFrame()

a.startLabelFrame("JSON Formatter")
a.addLabelFileEntry("Ugly JSON")
a.addButton("Format JSON", jsonBeautifier)
a.stopLabelFrame()

a.startLabelFrame("JSON Combiner")
a.addLabelFileEntry("JSON 1")
a.addLabelFileEntry("JSON 2")
a.addButton("Combine", combineJSON)
a.stopLabelFrame()

a.go()
