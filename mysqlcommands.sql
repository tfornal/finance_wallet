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

select * from assets;
commit;


drop table if exists investments; 

CREATE TABLE investments (
    id INT NOT NULL AUTO_INCREMENT,
    asset VARCHAR(255) NOT NULL,
    current_price FLOAT(20,10) NOT NULL,
    holdings FLOAT(20,10) not null,
    invested FLOAT (20,2) NOT NULL,
    current_value FLOAT (20,2) NOT NULL,
    pnl FLOAT (10,2) NOT NULL,
    owner_id INT NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY (owner_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE
);
show columns in investments;
LOAD DATA LOCAL INFILE '/home/tomasz/Programowanie/finance_wallet/crypto.csv' INTO TABLE finance_wallet.investments FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 ROWS; show warnings;
select * from investments;

alter table investments modify column holdings FLOAT(20,10);
commit;

