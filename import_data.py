import numpy as np
import pandas as pd
import json
from ast import literal_eval
import psycopg2

#load users
users = pd.read_json("users.json",lines=True)
users = users.fillna(0)
users["id"] = pd.DataFrame(users["_id"].values.tolist())["$oid"]
users["createdDate"] = pd.DataFrame(users["createdDate"].values.tolist())["$date"]
users["lastLogin"] = users["lastLogin"].str.get("$date").astype(object, errors='ignore')
users = users.convert_dtypes()
users = users.drop(["_id"],axis=1)
users.loc[users["lastLogin"].isna(), "lastLogin"] = 0
users["createdDate"] = pd.to_datetime(users["createdDate"],unit="ms")
users["lastLogin"] = pd.to_datetime(users["lastLogin"],unit="ms")

#load brands
brands = pd.read_json("brands.json",lines=True)
brands["id"] = pd.DataFrame(brands["_id"].values.tolist())["$oid"]
brands["cpg"] = pd.DataFrame(brands["cpg"].values.tolist())["$id"]
brands["cpg"] = pd.DataFrame(brands["cpg"].values.tolist())["$oid"]
brands['topBrand'] = brands['topBrand'].astype(bool)
brands = brands.drop(["_id"],axis=1)

#load receipts
receipts = pd.read_json("receipts.json",lines=True)
receipts = receipts.fillna(0)
receipts["id"] = pd.DataFrame(receipts["_id"].values.tolist())["$oid"]
receipts["createDate"] = pd.DataFrame(receipts["createDate"].values.tolist())["$date"]
receipts["createDate"] = pd.to_datetime(receipts["createDate"],unit="ms")
receipts["dateScanned"] = pd.DataFrame(receipts["dateScanned"].values.tolist())["$date"]
receipts["dateScanned"] = pd.to_datetime(receipts["dateScanned"],unit="ms")
receipts["finishedDate"] = receipts["finishedDate"].str.get("$date").astype(object, errors='ignore')
receipts["finishedDate"] = pd.to_datetime(receipts["finishedDate"],unit="ms")
receipts["modifyDate"] = receipts["modifyDate"].str.get("$date").astype(object, errors='ignore')
receipts["modifyDate"] = pd.to_datetime(receipts["modifyDate"],unit="ms")
receipts["purchaseDate"] = receipts["purchaseDate"].str.get("$date").astype(object, errors='ignore')
receipts["purchaseDate"] = pd.to_datetime(receipts["purchaseDate"],unit="ms")
receipts["pointsAwardedDate"] = receipts["pointsAwardedDate"].str.get("$date").astype(object, errors='ignore')
receipts["pointsAwardedDate"] = pd.to_datetime(receipts["pointsAwardedDate"],unit="ms")

receipts = receipts.convert_dtypes()

#extract receipt items from receipts
exploded = receipts.explode("rewardsReceiptItemList")
rewards_receipt_items = exploded[exploded["rewardsReceiptItemList"] != 0][["id","rewardsReceiptItemList"]]
rewards_receipt_items = rewards_receipt_items.reset_index(drop=True)
rewards_receipt_items["rewardsReceiptItemList"] = rewards_receipt_items["rewardsReceiptItemList"].astype(str)
rewards_receipt_items = pd.concat([rewards_receipt_items,
                                   pd.DataFrame(rewards_receipt_items["rewardsReceiptItemList"]
                                                .apply(literal_eval)
                                                .to_list())
                                   ],axis=1)
rewards_receipt_items = rewards_receipt_items.drop(["rewardsReceiptItemList"],axis=1)
rewards_receipt_items = rewards_receipt_items.rename(columns={"id":"receiptId"})
#pandas can't cast directly to an int if a data type isn't already a numeric, so cast to float first
rewards_receipt_items["pointsEarned"] = rewards_receipt_items["pointsEarned"].fillna(0).astype(float).astype(int)
rewards_receipt_items = rewards_receipt_items.convert_dtypes()

#drop item list now that it's been created in a separate table
receipts = receipts.drop(["_id","rewardsReceiptItemList"],axis=1)

#rearrange columns
users       = users[["id","state","createdDate","lastLogin","role","active","signUpSource"]]
brands      = brands[["id","barcode","brandCode","category","categoryCode","cpg","topBrand","name"]]
receipts    = receipts[["id","bonusPointsEarned","bonusPointsEarnedReason","createDate","dateScanned",
                     "finishedDate","modifyDate","pointsAwardedDate","purchaseDate","purchasedItemCount",
                     "rewardsReceiptStatus","totalSpent","userId"]]
rewards_receipt_items = rewards_receipt_items[["receiptId","barcode","brandCode","description",
                     "finalPrice","itemPrice","discountedItemPrice","needsFetchReview","partnerItemId",
                     "pointsNotAwardedReason","pointsPayerId","preventTargetGapPoints","quantityPurchased",
                     "rewardsGroup","rewardsProductPartnerId","targetPrice","userFlaggedBarcode",
                     "userFlaggedNewItem","userFlaggedPrice","userFlaggedQuantity","metabriteCampaignId",
                     "originalMetaBriteDescription","originalMetaBriteBarcode",
                     "originalMetaBriteQuantityPurchased","competitiveProduct","competitorRewardsGroup",
                     "originalReceiptItemText","originalFinalPrice","itemNumber","deleted","priceAfterCoupon",
                     "pointsEarned"
                     ]]

#create CSVs
users.to_csv("users.csv", index=False)
brands.to_csv("brands.csv", index=False)
receipts.to_csv("receipts.csv", index=False)
rewards_receipt_items.to_csv("rewards_receipt_items.csv", index=False)

#create and prepare tables
conn = psycopg2.connect(database="fetch_test",
                        user="postgres",
                        password="postgres",
                        host="localhost",
                        port="5432")
conn.autocommit = True
cursor = conn.cursor()
with open("./sql/create_tables.sql") as f:
    sql = f.read()
    cursor.execute(sql)

#load CSVs to postgres
with open ("./users.csv") as f:
    next(f)
    cursor.copy_from(f, "users", sep=",")

with open ("./brands.csv") as f:
    next(f)
    cursor.copy_expert("copy brandbarcodes from stdin (format csv)",f) #copy_from doesn't like quotes
    
with open("./receipts.csv") as f:
    next(f)
    cursor.copy_expert("copy receipts from stdin (format csv)",f) #copy_from doesn't like quotes

with open("./rewards_receipt_items.csv") as f:
    next(f)
    cursor.copy_expert("copy rewardsreceiptitems from stdin (format csv)",f) #copy_from doesn't like quotes