CREATE TABLE IF NOT EXISTS receipts (
    id TEXT NOT NULL,
    bonusPointsEarned INT,
    bonusPointsEarnedReason TEXT,
    createDate TIMESTAMP,
    dateScanned TIMESTAMP,
    finishedDate TIMESTAMP,
    modifyDate TIMESTAMP,
    pointsAwardedDate TIMESTAMP,
    purchaseDate TIMESTAMP,
    purchasedItemCount INT,
    rewardsReceiptStatus TEXT,
    totalSpent NUMERIC,
    userId TEXT,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS users (
    id TEXT NOT NULL,
    state TEXT,
    createdDate TIMESTAMP,
    lastLogin TIMESTAMP,
    role TEXT,
    active BOOLEAN,
    signupSource text
);

CREATE TABLE IF NOT EXISTS rewardsReceiptItems (
    receiptId TEXT not NULL,
    barcode TEXT,
    brandCode TEXT,
    description TEXT,
    finalPrice NUMERIC,
    itemPrice NUMERIC,
    discountedItemPrice NUMERIC,
    needsFetchReview BOOLEAN,
    partnerItemId TEXT,
    pointsNotAwardedReason TEXT,
    pointsPayerId TEXT,
    preventTargetGapPoints BOOLEAN,
    quantityPurchased INT,
    rewardsGroup TEXT,
    rewardsProductPartnerId TEXT,
    targetPrice NUMERIC,
    userFlaggedBarcode TEXT,
    userFlaggedNewItem BOOLEAN,
    userFlaggedPrice NUMERIC,
    userFlaggedQuantity INT,
    metabriteCampaignId TEXT,
    originalMetaBriteDescription TEXT,
    originalMetaBriteBarcode TEXT,
    originalMetaBriteQuantityPurchased INT,
    competitiveProduct BOOLEAN,
    competitorRewardsGroup TEXT,
    originalReceiptItemText TEXT,
    originalFinalPrice NUMERIC,
    itemNumber TEXT,
    deleted BOOLEAN,
    priceAfterCoupon NUMERIC,
    pointsEarned INT
);

CREATE TABLE IF NOT EXISTS brandBarcodes (
    id TEXT NOT NULL,
    barcode TEXT,
    brandCode TEXT,
    category TEXT,
    categoryCode TEXT,
    cpg TEXT,
    topBrand BOOLEAN,
    name TEXT,
    PRIMARY KEY (id)
);