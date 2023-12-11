use finance_wallet;
select * from wallet;

drop table if exists wallet; 

use finance_wallet; 
CREATE TABLE wallet (
    id INT NOT NULL AUTO_INCREMENT,
    title VARCHAR(255) NOT NULL,
    price FLOAT NOT NULL,
    category VARCHAR(255) NOT NULL,
    date DATE DEFAULT current_date,
    owner_id INT NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY (owner_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE
);




CREATE TABLE credits (
    id INT NOT NULL AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    price FLOAT NOT NULL,
    category VARCHAR(255) NOT NULL,
    owner_id INT NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY (owner_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE
);

show tables;

LOAD DATA LOCAL INFILE '/home/tomasz/Programowanie/finance_wallet/wydatki.csv' INTO TABLE finance_wallet.wallet FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 ROWS; show warnings;


alter table assets add column percentage_share float after asset_value_pln;