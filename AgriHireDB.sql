DROP SCHEMA IF EXISTS AgriHireDB;

CREATE DATABASE AgriHireDB;
USE AgriHireDB;

/* ----- Create the tables: ----- */
CREATE TABLE IF NOT EXISTS account (
  account_id int NOT NULL AUTO_INCREMENT primary key,
  username varchar(100) NOT NULL unique,
  password varchar(255) NOT NULL,
  role varchar(50) default 'customer'
);

CREATE TABLE IF NOT EXISTS store (
    store_id INT AUTO_INCREMENT PRIMARY KEY,
    store_name VARCHAR(50) NOT NULL,
    address VARCHAR(50) NOT NULL,
    phone VARCHAR(100) NOT NULL,
	city VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS customer (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    last_name VARCHAR(50) NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL,
	address VARCHAR(100) NOT NULL,
    date_of_Birth DATE NOT NULL,
    join_date DATE DEFAULT (CURDATE()),
    image VARCHAR(255) default 'default.png'  comment 'ID',
	store_id int,
    username VARCHAR(100) unique,
    FOREIGN KEY (username) REFERENCES account(username) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (store_id) REFERENCES store(store_id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS staff (
    staff_id INT AUTO_INCREMENT PRIMARY KEY,
    last_name VARCHAR(50) NOT NULL,
    first_name VARCHAR(50) NOT NULL,
	email VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL,
	address VARCHAR(100) NOT NULL,
    position VARCHAR(50) NOT NULL,
    image VARCHAR(255) default 'default.png',
	username VARCHAR(100) unique,
    store_id int not null,
    status VARCHAR(50) default 'active',
	FOREIGN KEY (username) REFERENCES account(username) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (store_id) REFERENCES store(store_id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS management (
    management_id INT AUTO_INCREMENT PRIMARY KEY,
    last_name VARCHAR(50) NOT NULL,
    first_name VARCHAR(50) NOT NULL,
	email VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL,
	address VARCHAR(100) NOT NULL,
    position VARCHAR(50) NOT NULL,
    image VARCHAR(255) default 'default.png',
    username VARCHAR(100) unique,
	FOREIGN KEY (username) REFERENCES account(username) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS notification (
    notification_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    title VARCHAR(50) NOT NULL,
	content text NOT NULL,
	FOREIGN KEY (customer_id) REFERENCES customer(customer_id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS message (
    message_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    staff_id INT NOT NULL,
	subject VARCHAR(50) NOT NULL,
    content text not null,
    date timestamp DEFAULT CURRENT_TIMESTAMP,
	FOREIGN KEY (customer_id) REFERENCES customer(customer_id) ON DELETE CASCADE ON UPDATE CASCADE,
	FOREIGN KEY (staff_id) REFERENCES staff(staff_id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS promotion (
    promotion_id INT AUTO_INCREMENT PRIMARY KEY,
    promotion_name varchar(255) not null,
    description text not null,
    start_day date NOT NULL,
	end_day date NOT NULL,
    discount_rate Int not null,
    store_id INT not null,
	FOREIGN KEY (store_id) REFERENCES store(store_id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS news (
    news_id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(50) NOT NULL,
    content text not null,
	create_time DATE DEFAULT (CURDATE()),
    store_id INT,
	FOREIGN KEY (store_id) REFERENCES store(store_id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS category (
    category_id INT AUTO_INCREMENT PRIMARY KEY,
    category_name VARCHAR(255) NOT NULL,
    image varchar(255) not null
);


CREATE TABLE IF NOT EXISTS store_equipment (
    equipment_id INT not null AUTO_INCREMENT PRIMARY KEY,
    name varchar(255) not null,
    specifications TEXT not null,
    cost decimal not null,
    image varchar(255) not null,
    hire_cost INT not null,
	min_hire_period  INT NOT NULL,
    max_hire_period INT not null,
    category_id INT,
    store_id int not null,
	FOREIGN KEY (category_id) REFERENCES category(category_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (store_id) REFERENCES store(store_id) ON DELETE CASCADE ON UPDATE CASCADE
);


CREATE TABLE IF NOT EXISTS inventory (
    serial_number INT AUTO_INCREMENT PRIMARY KEY,
    store_id int not null,  
	equipment_id INT not null,
    purchase_date DATE not null,   
    status varchar(255) not null  Comment 'available, repair, broken, rent',
	FOREIGN KEY (equipment_id) REFERENCES store_equipment(equipment_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (store_id) REFERENCES store(store_id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS service_record (
    service_id INT AUTO_INCREMENT PRIMARY KEY,
    serial_number int not null,
	start_date datetime not null,
    end_date datetime not null,
    details varchar(255) not null,
    service_cost decimal(10,2) not null,
	FOREIGN KEY (serial_number) REFERENCES inventory(serial_number) ON DELETE CASCADE ON UPDATE CASCADE
);


CREATE TABLE IF NOT EXISTS shoppingcart (
    customer_id INT not null,
    equipment_id int not null,   
    hire_cost decimal not null,
    start_date date not null,
    end_date date not null,
    quantity int not null,
    primary key(customer_id,equipment_id),
	FOREIGN KEY (customer_id) REFERENCES customer(customer_id) ON DELETE CASCADE ON UPDATE CASCADE,
	FOREIGN KEY (equipment_id) REFERENCES store_equipment(equipment_id) ON DELETE CASCADE ON UPDATE CASCADE
);



							
CREATE TABLE IF NOT EXISTS booking (
    booking_id INT AUTO_INCREMENT PRIMARY KEY,
	customer_id INT NOT NULL,
	store_id INT,       
    total_amount decimal(10,2) not null,
    booking_date date not null,
    status varchar(45) not null default 'unpaid' comment 'paid,unpaid,cancelled',
    FOREIGN KEY (customer_id) REFERENCES customer(customer_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (store_id) REFERENCES store(store_id) ON DELETE CASCADE ON UPDATE CASCADE
);

							
CREATE TABLE IF NOT EXISTS booking_detail (
    detail_id INT AUTO_INCREMENT PRIMARY KEY,
	booking_id INT NOT NULL,
	equipment_id INT not null,           
	start_date date not null,   
    end_date date not null,
    total decimal(10,2) not null,
    quantity int not null,         
    FOREIGN KEY (booking_id) REFERENCES booking(booking_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (equipment_id) REFERENCES store_equipment(equipment_id) ON DELETE CASCADE ON UPDATE CASCADE
);


CREATE TABLE IF NOT EXISTS payment (
    payment_id INT AUTO_INCREMENT PRIMARY KEY,
	booking_id INT NOT NULL,
    amount decimal(10,2) not null,
    payment_date date not null,
    status varchar(45) not null,
    FOREIGN KEY (booking_id) REFERENCES booking(booking_id) ON DELETE CASCADE ON UPDATE CASCADE
);


CREATE TABLE IF NOT EXISTS in_out_record (
    record_id INT AUTO_INCREMENT PRIMARY KEY,
	detail_id INT NOT NULL,
    pickup_time date,
    return_time date,
    FOREIGN KEY (detail_id) REFERENCES booking_detail(detail_id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS feedback (
    feedback_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    email VARCHAR(50) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    subject VARCHAR(20) NOT NULL,
	 create_time datetime DEFAULT CURRENT_TIMESTAMP,
	 customer_id INT not null,
	 store_id INT not null,
	 FOREIGN KEY (customer_id) REFERENCES customer(customer_id) ON DELETE CASCADE ON UPDATE CASCADE,
	 FOREIGN KEY (store_id) REFERENCES store(store_id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS feedback_exchange (
    exchange_id INT AUTO_INCREMENT PRIMARY KEY,
    sender_id  INT not null,
	create_time datetime DEFAULT CURRENT_TIMESTAMP,
	content LONGTEXT not null,
    feedback_id  INT not null,
    FOREIGN KEY (feedback_id) REFERENCES feedback(feedback_id) ON DELETE CASCADE ON UPDATE CASCADE

);

CREATE TABLE IF NOT EXISTS customer_report(
    name   varchar(45) not null,
    email    varchar(45) not null,
    equipment varchar(45) not null,
    description varchar(45) not null,
    photo varchar(45)
);

CREATE TABLE IF NOT EXISTS customer_request(
    equipment_id   varchar(45) not null,
    name   varchar(45) not null,
    email    varchar(45) not null,
    equipment varchar(45) not null,
    reason varchar(45) not null,
    store varchar(45) not null
);



INSERT INTO store (store_name, address, phone, city) VALUES
('Auckland Store', '123 Queen St', '093012345', 'Auckland'),
('Wellington Store', '456 King St', '044012345', 'Wellington'),
('Christchurch Store', '789 High St', '033012345', 'Christchurch'),
('Tauranga Store', '210 Hexagon Rd', '075678901', 'Tauranga'),
('Dunedin Store', '432 Pentagon Rd', '034567890', 'Dunedin'),
('Napier Store', '678 Rhombus Rd', '068901234', 'Napier');


INSERT INTO account (username, password, role) VALUES
('customer1', 'pbkdf2:sha256:600000$ASyPDn44CH5CsN24$de93cd54bad8addc21aa95d34ef24a796e01d2965e4f71afb39cab9d90f7b81a', 'customer'),
('customer2', 'pbkdf2:sha256:600000$ASyPDn44CH5CsN24$de93cd54bad8addc21aa95d34ef24a796e01d2965e4f71afb39cab9d90f7b81a', 'customer'),
('customer3', 'pbkdf2:sha256:600000$ASyPDn44CH5CsN24$de93cd54bad8addc21aa95d34ef24a796e01d2965e4f71afb39cab9d90f7b81a', 'customer'),
('staff1', 'pbkdf2:sha256:600000$ASyPDn44CH5CsN24$de93cd54bad8addc21aa95d34ef24a796e01d2965e4f71afb39cab9d90f7b81a', 'staff'),
('staff2', 'pbkdf2:sha256:600000$ASyPDn44CH5CsN24$de93cd54bad8addc21aa95d34ef24a796e01d2965e4f71afb39cab9d90f7b81a', 'staff'),
('staff3', 'pbkdf2:sha256:600000$ASyPDn44CH5CsN24$de93cd54bad8addc21aa95d34ef24a796e01d2965e4f71afb39cab9d90f7b81a', 'staff'),
('staff4', 'pbkdf2:sha256:600000$ASyPDn44CH5CsN24$de93cd54bad8addc21aa95d34ef24a796e01d2965e4f71afb39cab9d90f7b81a', 'staff'),
('staff5', 'pbkdf2:sha256:600000$ASyPDn44CH5CsN24$de93cd54bad8addc21aa95d34ef24a796e01d2965e4f71afb39cab9d90f7b81a', 'staff'),
('staff6', 'pbkdf2:sha256:600000$ASyPDn44CH5CsN24$de93cd54bad8addc21aa95d34ef24a796e01d2965e4f71afb39cab9d90f7b81a', 'staff'),
('local1', 'pbkdf2:sha256:600000$ASyPDn44CH5CsN24$de93cd54bad8addc21aa95d34ef24a796e01d2965e4f71afb39cab9d90f7b81a', 'local_manager'),
('local2', 'pbkdf2:sha256:600000$ASyPDn44CH5CsN24$de93cd54bad8addc21aa95d34ef24a796e01d2965e4f71afb39cab9d90f7b81a', 'local_manager'),
('local3', 'pbkdf2:sha256:600000$ASyPDn44CH5CsN24$de93cd54bad8addc21aa95d34ef24a796e01d2965e4f71afb39cab9d90f7b81a', 'local_manager'),
('local4', 'pbkdf2:sha256:600000$ASyPDn44CH5CsN24$de93cd54bad8addc21aa95d34ef24a796e01d2965e4f71afb39cab9d90f7b81a', 'local_manager'),
('local5', 'pbkdf2:sha256:600000$ASyPDn44CH5CsN24$de93cd54bad8addc21aa95d34ef24a796e01d2965e4f71afb39cab9d90f7b81a', 'local_manager'),
('local6', 'pbkdf2:sha256:600000$ASyPDn44CH5CsN24$de93cd54bad8addc21aa95d34ef24a796e01d2965e4f71afb39cab9d90f7b81a', 'local_manager'),
('admin1', 'pbkdf2:sha256:600000$ASyPDn44CH5CsN24$de93cd54bad8addc21aa95d34ef24a796e01d2965e4f71afb39cab9d90f7b81a', 'systems_admin'),
('national1', 'pbkdf2:sha256:600000$ASyPDn44CH5CsN24$de93cd54bad8addc21aa95d34ef24a796e01d2965e4f71afb39cab9d90f7b81a', 'national_manager');


INSERT INTO customer (last_name, first_name, email, phone, address, date_of_Birth, join_date, store_id, username) VALUES
('Doe', 'John', 'john.doe@example.com', '0211234567', '123 Queen St, Auckland', STR_TO_DATE('08-05-1995', '%d-%m-%Y'), CURDATE(), 1, 'customer1'),
('Doe', 'Jane', 'jane.doe@example.com', '0217654321', '456 King St, Wellington', STR_TO_DATE('05-08-1992', '%d-%m-%Y'), CURDATE(), 2, 'customer2'),
('Beam', 'Jim', 'jim.beam@example.com', '0229876543', '789 High St, Christchurch', STR_TO_DATE('05-08-1989', '%d-%m-%Y'), CURDATE(), 3, 'customer3');


INSERT INTO staff (last_name, first_name, email, phone, address, position,image, store_id, username) VALUES
('Jones', 'Alice', 'alice.jones@example.com', '0215556666', '321 Circle Rd, Auckland', 'Staff ','profile-1.png', 1, 'staff1'),
('Smith', 'Bob', 'bob.smith@example.com', '0214447777', '654 Triangle Rd, Wellington','Staff', 'profile-2.png',2, 'staff2'),
('Johnson', 'Alice', 'alice.johnson@example.com', '0215558888', '123 Square St, Christchurch', 'Staff', 'profile-3.png', 3, 'staff3'),
('Brown', 'Charlie', 'charlie.brown@example.com', '0216669999', '789 Circle Ave, Tauranga', 'Staff', 'profile-4.png', 4, 'staff4'),
('Davis', 'Diana', 'diana.davis@example.com', '0217770000', '456 Oval Rd, Dunedin', 'Staff', 'profile-5.png', 5, 'staff5'),
('Wilson', 'Eve', 'eve.wilson@example.com', '0218881111', '321 Rectangle Blvd, Napier', 'Staff', 'profile-6.png', 6, 'staff6'),
('White', 'Carol', 'carol.white@example.com', '0213338888', '987 Square Rd, Auckland','Local Manager','profile-7.png', 1, 'local1'),
('Brown', 'Dave', 'dave.brown@example.com', '0212229999', '210 Hexagon Rd, Wellington','Local Manager', 'profile-8.png', 2, 'local2'),
('Green', 'David', 'david.green@example.com', '0212227777', '123 Hexagon St, Christchurch', 'Local Manager', 'profile-9.png', 3, 'local3'),
('Black', 'Emma', 'emma.black@example.com', '0211116666', '654 Pentagon Ave, Tauranga', 'Local Manager', 'profile-10.png', 4, 'local4'),
('Brown', 'Frank', 'frank.brown@example.com', '0214445555', '789 Rhombus Blvd, Dunedin', 'Local Manager', 'profile-11.png', 5, 'local5'),
('Grey', 'Grace', 'grace.grey@example.com', '0215554444', '321 Trapezoid Ln, Napier', 'Local Manager', 'profile-12.png', 6, 'local6');


INSERT INTO management (last_name, first_name, email, phone, address, position,image, username) VALUES
('Black', 'Eve', 'eve.black@example.com', '0211110000', '432 Pentagon Rd, Dunedin', 'Systems Administrator','profile-5.png', 'admin1'),
('Green', 'Frank', 'frank.green@example.com', '0210001111', '678 Rhombus Rd, Napier', 'National Manager', 'profile-6.png','national1');

INSERT INTO category (category_name,image) Values
('Tractors', 'categories_img_01.jpg'),
('Mixers', 'categories_img_02.jpg'),
('Lawn mowers', 'categories_img_03.jpg'),
('Chainsaws', 'categories_img_04.jpg'),
('Grinders', 'categories_img_05.jpg'),
('Telehandlers', 'categories_img_06.jpg');

INSERT INTO store_equipment (name,specifications,cost,image,hire_cost,min_hire_period,max_hire_period,category_id,store_id) Values
('TRACTOR - 25 HP', 'General purpose tractor with applications that include aerating and topdressing with the appropriate attachments.',100000,'product-1.jpg',305,1,7,1,1),
('TRACTOR BROOM - 30HP', 'Road Sweeping unit ideal for road construction/ infrastructure project work.',100000,'product-2.jpg',399,1,7,1,1),
('TRACTOR - 45HP', 'Heavy duty tractor with optional slasher attachment. Suitable for large areas of clearing and vegetation removal for farm and property use, as well as land and fire prevention preparation.',100000,'product-3.jpg',497,1,7,1,1),
('TRACTOR - REAR GRADER BLADE', 'These units are ideal for topping and mowing larger sections and;paddocks.',100000,'product-9.jpg',107,1,7,1,1),
('TRACTOR - SLASHER ATTACH', 'Rear grader attachment for leveling soil or paths.',100000,'product-10.jpg',134,1,7,1,1),


('MIXER PUMP LARGE DIESEL', 'A large diesel pump with hydraulic worm drive that pumps up to 40m vertically. Suited to thick and free flowing media, with fully controllable delivery flow. Handles wet mortar only with grain size up 6mm and has an adjustable mixing speed.',100000,'product-4.jpg',70,1,7,2,1),
('CONCRETE MIXER - BARROW', '
A handy 240V electric powered concrete mixer ideal for smaller building projects. Can double as both a mixer and wheel barrow all in one with a 2 cu ft. capacity. Use on the stand provided or remove and use to mix and barrow the mixture into place.',100000,'product-11.jpg',85,1,7,2,1),
('CONCRETE MIXER - PETROL TOWABLE', 'A handy 4-Stroke petrol powered concrete mixer ideal for smaller building projects. Trailer mounted for easy transport to and from site.',100000,'product-12.jpg',99,1,7,2,1),
('CONCRETE MIXER - PETROL', '
A handy 4-Stroke petrol powered concrete mixer ideal for smaller building projects that is mounted on wheels for ease placement on site.',100000,'product-13.jpg',90,1,7,2,1),
('MIXER PUMP 240L DIESEL', '
Larger towable mixer pump with powerful stage 5 diesel motor. Suited to a range of high volume grout, plaster and mortar applications, with aggregate up to 8mm.',100000,'product-14.jpg',90,1,7,2,1),


('LAWN DETHATCHER CORDLESS', 'A light-weight battery-powered, cordless scarifier with a 2-in-1 function and easy blade shift. The easily adjusted working depth, together with a powerful engine, efficiently remove matted thatch and moss from the lawn.',100000,'product-5.jpg',114,1,7,3,1),
('LAWN MOWER - 450MM DOMESTIC', 'A commercial quality lawn mower and catcher for a quick and tidy job. The high arch alloy body ensures long and damp grass is cut and thrown into the catcher. SImple and easy to start and use.',100000,'product-15.jpg',61,1,7,3,1),
('LAWN ROTARY HOE', '
A tough, walk behind, petrol powered machine ideal for one person to break up hard soil and clay for initial lawn and garden preparation. Counter rotating tines break up the most difficult soil, clay or sod.',100000,'product-16.jpg',160,1,7,3,1),
('LAWN CORER - PETROL', 'This corer is self propelled, designed to allow air into the root system. This process helps with watering and fertilising to promote rejuvenation.',100000,'product-17.jpg',189,1,7,3,1),
('LAWN MOWER 600MM', 'Self propelled grass slasher designed to level brush, tall weeds, saplings and heavy vegetation with ease. Featuring big wheels and a powerful motor, these self-propelled slashers are popular for reducing fire hazards and cleaning up large areas.
',100000,'product-18.jpg',124,1,7,3,1),
('LAWN MOWER - ZERO TURN (52IN)', 'A popular self propelled landscaping machine with depth adjustment for harvesting or removing turf. Cuts ready to roll, up to 900sqm of turf per hour.
',100000,'product-19.jpg',323,1,7,3,1),
('LAWN MOWER - ZERO TURN (54IN)', 'A popular self propelled landscaping machine with depth adjustment for harvesting or removing turf. Cuts ready to roll, up to 900sqm of turf per hour.
',100000,'product-20.jpg',294,1,7,3,1),
('LAWN ROTARY TILLER - PETROL', 'Light duty cultivator for establishing garden beds and lawns, ideal for soft or sandy soil. Simple to operate, features a 4-stroke motor.',100000,'product-21.jpg',117,1,7,3,1),
('LAWN TRIMMER MOWER', 'Offset frame allows trimming right up against foundations',100000,'product-22.jpg',115,1,7,3,1),


('CHAINSAW - 450MM (18IN) PETROL', 'Professional 2 stroke chainsaw with a powerful motor suitable for use in remote locations. Ideal for cutting firewood, tree lopping and trimming.',100000,'product-6.jpg',125,1,7,4,1),
('CHAINSAW - 450MM (18IN) CORDLESS', 'Power through your outdoor tasks with a reliable battery chainsaw. Cordless convenience, eco-friendly performance, and long-lasting power make it your go-to tool for effortless cutting and pruning.',100000,'product-23.jpg',144,1,7,4,1),
('CHAINSAW - 300MM (12IN) PETROL', 'Professional 2 stroke chainsaw with a powerful motor suitable for use in remote locations. Ideal for cutting firewood, tree lopping and trimming.',100000,'product-24.jpg',132,1,7,4,1),
('CHAINSAW - 300MM (12IN) CORDLESS', 'Professional 2 stroke chainsaw with a powerful motor suitable for use in remote locations. Ideal for cutting firewood, tree lopping and trimming.',100000,'product-25.jpg',108,1,7,4,1),
('CONCRETE CHAINSAW - 400MM (16IN) PETROL', 'A purpose built, 2 stroke motorised chainsaw featuring a diamond tipped blade. It is designed to cut concrete, stone and masonry using a water feed for lubrication and dust control. It features an electronic ignition for easy starting and maximum productivity.
',100000,'product-26.jpg',331,1,7,4,1),
('CONCRETE CHAINSAW - 400MM (16IN) HYDRAULIC', 'This high powered hydraulic chainsaw is capable of cutting reinforced concrete to a maximum depth of 350mm. Makes flush cuts and square cutting easy and features a wet cutting system. No kickback.
',100000,'product-27.jpg',331,1,7,4,1),


('CHIPPER - 150MM DIESEL', '
A fast and efficient, towable chipper for recycling branches. Turns tree and shrub prunings into mulch or compost. Reduces tree prunings to a manageable size and is capable of chipping branches up to 150 mm in diameter.',100000,'product-7.jpg',367,1,7,5,1),
('BRISTLE BLASTER - BATTERY', '
The Bristle Blaster combines the ability to produce an abrasive blasted finish with the high mobility and flexibility of a portable hand-held tool.',100000,'product-28.jpg',88,1,7,5,1),
('CHIPPER - 75MM PETROL TOWABLE', '
A fast and efficient, road towable chipper for recycling branches. Turns tree and shrub prunings into mulch or compost. Reduces tree prunings to a manageable size and is capable of chipping branches up to 75mm in diameter.
',100000,'product-29.jpg',231,1,7,5,1),
('GRINDER - ANGLE 225MM', '
A versatile, time saving tool that uses carborundum wheels for; cutting or grinding steel or masonry. Popular applications include light demolition, surface preparation and maintenance, trimming; slate, tiles and pavers.
',100000,'product-30.jpg',64,1,7,5,1),
('GRINDER - ANGLE 115MM TO 125MM', '
A versatile, time saving tool that uses carborundum wheels for; cutting or grinding steel or masonry. Popular applications include light demolition, surface preparation and maintenance, trimming; slate, tiles and pavers.
',100000,'product-31.jpg',46,1,7,5,1),
('DRILL - RIGHT ANGLE', '
Trade quality right angle drill for drilling in areas that a conventional drill wont reach.
',100000,'product-32.jpg',47,1,7,5,1),
('STUMP GRINDER - PETROL', 'Undercut unsightly or dangerous tree stumps and roots to below ground level. A high performance machine featuring tungsten carbide cutters for fast results. Grinds 300mm high stumps to 250mm below ground.
',100000,'product-33.jpg',280,1,7,5,1),
('STUMP GRINDER - TRACKED LARGE', 'Stump grinders use a rotating cutting disc to chip away at tree stumps to below ground level.
',100000,'product-34.jpg',404,1,7,5,1),


('TELEHANDLER - 4T 9.5M', '
A versatile lifting solution for construction and industrial projects. With its impressive capacity and reach, it ensures efficient material handling in various work environments.',100000,'product-8.jpg',800,1,7,6,1),
('TELEHANDLER - 2.5T', '
Extremely versatile telescopic material handling vehicle, for heavy loads, to be transported on all types of terrain.',100000,'product-35.jpg',411,1,7,6,1),
('TELEHANDLER - 3.8T 8M', '
Extremely versatile telescopic material handling vehicle, for heavy loads, to be transported on all types of terrain.',100000,'product-36.jpg',602,1,7,6,1),


('TRACTOR - 25 HP', 'General purpose tractor with applications that include aerating and topdressing with the appropriate attachments.',100000,'product-1.jpg',305,1,7,1,2),
('MIXER PUMP LARGE DIESEL', 'A large diesel pump with hydraulic worm drive that pumps up to 40m vertically. Suited to thick and free flowing media, with fully controllable delivery flow. Handles wet mortar only with grain size up 6mm and has an adjustable mixing speed.',100000,'product-4.jpg',70,1,7,2,2),
('LAWN DETHATCHER CORDLESS', 'A light-weight battery-powered, cordless scarifier with a 2-in-1 function and easy blade shift. The easily adjusted working depth, together with a powerful engine, efficiently remove matted thatch and moss from the lawn.',100000,'product-5.jpg',114,1,7,3,2),

('CHAINSAW - 450MM (18IN) PETROL', 'Professional 2 stroke chainsaw with a powerful motor suitable for use in remote locations. Ideal for cutting firewood, tree lopping and trimming.
',100000,'product-6.jpg',125,1,7,4,2),

('CHIPPER - 150MM DIESEL', '
A fast and efficient, towable chipper for recycling branches. Turns tree and shrub prunings into mulch or compost. Reduces tree prunings to a manageable size and is capable of chipping branches up to 150 mm in diameter.',100000,'product-7.jpg',367,1,7,5,2),

('TELEHANDLER - 4T 9.5M', '
A versatile lifting solution for construction and industrial projects. With its impressive capacity and reach, it ensures efficient material handling in various work environments.',100000,'product-8.jpg',800,1,7,6,2),


('TRACTOR BROOM - 30HP', 'Road Sweeping unit ideal for road construction/ infrastructure project work.',100000,'product-2.jpg',399,1,7,1,2),
('TRACTOR - 45HP', 'Heavy duty tractor with optional slasher attachment. Suitable for large areas of clearing and vegetation removal for farm and property use, as well as land and fire prevention preparation.',100000,'product-3.jpg',497,1,7,1,2),
('TRACTOR - REAR GRADER BLADE', 'These units are ideal for topping and mowing larger sections and;paddocks.',100000,'product-9.jpg',107,1,7,1,2),
('CONCRETE MIXER - PETROL TOWABLE', 'A handy 4-Stroke petrol powered concrete mixer ideal for smaller building projects. Trailer mounted for easy transport to and from site.',100000,'product-12.jpg',99,1,7,2,2),
('CONCRETE MIXER - PETROL', '
A handy 4-Stroke petrol powered concrete mixer ideal for smaller building projects that is mounted on wheels for ease placement on site.',100000,'product-13.jpg',90,1,7,2,2),
('MIXER PUMP 240L DIESEL', '
Larger towable mixer pump with powerful stage 5 diesel motor. Suited to a range of high volume grout, plaster and mortar applications, with aggregate up to 8mm.',100000,'product-14.jpg',90,1,7,2,2),

('LAWN MOWER - ZERO TURN (52IN)', 'A popular self propelled landscaping machine with depth adjustment for harvesting or removing turf. Cuts ready to roll, up to 900sqm of turf per hour.
',100000,'product-19.jpg',323,1,7,3,2),
('LAWN MOWER - ZERO TURN (54IN)', 'A popular self propelled landscaping machine with depth adjustment for harvesting or removing turf. Cuts ready to roll, up to 900sqm of turf per hour.
',100000,'product-20.jpg',294,1,7,3,2),
('LAWN ROTARY TILLER - PETROL', 'Light duty cultivator for establishing garden beds and lawns, ideal for soft or sandy soil. Simple to operate, features a 4-stroke motor.',100000,'product-21.jpg',117,1,7,3,2),
('LAWN TRIMMER MOWER', 'Offset frame allows trimming right up against foundations',100000,'product-22.jpg',115,1,7,3,2),
('CHAINSAW - 300MM (12IN) PETROL', 'Professional 2 stroke chainsaw with a powerful motor suitable for use in remote locations. Ideal for cutting firewood, tree lopping and trimming.',100000,'product-24.jpg',132,1,7,4,2),
('CHAINSAW - 300MM (12IN) CORDLESS', 'Professional 2 stroke chainsaw with a powerful motor suitable for use in remote locations. Ideal for cutting firewood, tree lopping and trimming.',100000,'product-25.jpg',108,1,7,4,2),
('BRISTLE BLASTER - BATTERY', '
The Bristle Blaster combines the ability to produce an abrasive blasted finish with the high mobility and flexibility of a portable hand-held tool.',100000,'product-28.jpg',88,1,7,5,2),
('CHIPPER - 75MM PETROL TOWABLE', '
A fast and efficient, road towable chipper for recycling branches. Turns tree and shrub prunings into mulch or compost. Reduces tree prunings to a manageable size and is capable of chipping branches up to 75mm in diameter.
',100000,'product-29.jpg',231,1,7,5,2),
('GRINDER - ANGLE 225MM', '
A versatile, time saving tool that uses carborundum wheels for; cutting or grinding steel or masonry. Popular applications include light demolition, surface preparation and maintenance, trimming; slate, tiles and pavers.
',100000,'product-30.jpg',64,1,7,5,2),
('GRINDER - ANGLE 115MM TO 125MM', '
A versatile, time saving tool that uses carborundum wheels for; cutting or grinding steel or masonry. Popular applications include light demolition, surface preparation and maintenance, trimming; slate, tiles and pavers.
',100000,'product-31.jpg',46,1,7,5,2),
('TELEHANDLER - 3.8T 8M', '
Extremely versatile telescopic material handling vehicle, for heavy loads, to be transported on all types of terrain.',100000,'product-36.jpg',602,1,7,6,2),



('TRACTOR - 25 HP', 'General purpose tractor with applications that include aerating and topdressing with the appropriate attachments.',100000,'product-1.jpg',305,1,7,1,3),
('MIXER PUMP LARGE DIESEL', 'A large diesel pump with hydraulic worm drive that pumps up to 40m vertically. Suited to thick and free flowing media, with fully controllable delivery flow. Handles wet mortar only with grain size up 6mm and has an adjustable mixing speed.',100000,'product-4.jpg',70,1,7,2,3),
('LAWN DETHATCHER CORDLESS', 'A light-weight battery-powered, cordless scarifier with a 2-in-1 function and easy blade shift. The easily adjusted working depth, together with a powerful engine, efficiently remove matted thatch and moss from the lawn.',100000,'product-5.jpg',114,1,7,3,3),

('CHAINSAW - 450MM (18IN) PETROL', 'Professional 2 stroke chainsaw with a powerful motor suitable for use in remote locations. Ideal for cutting firewood, tree lopping and trimming.
',100000,'product-6.jpg',125,1,7,4,3),

('CHIPPER - 150MM DIESEL', '
A fast and efficient, towable chipper for recycling branches. Turns tree and shrub prunings into mulch or compost. Reduces tree prunings to a manageable size and is capable of chipping branches up to 150 mm in diameter.',100000,'product-7.jpg',367,1,7,5,3),

('TELEHANDLER - 4T 9.5M', '
A versatile lifting solution for construction and industrial projects. With its impressive capacity and reach, it ensures efficient material handling in various work environments.',100000,'product-8.jpg',800,1,7,6,3),


('TRACTOR BROOM - 30HP', 'Road Sweeping unit ideal for road construction/ infrastructure project work.',100000,'product-2.jpg',399,1,7,1,3),
('TRACTOR - 45HP', 'Heavy duty tractor with optional slasher attachment. Suitable for large areas of clearing and vegetation removal for farm and property use, as well as land and fire prevention preparation.',100000,'product-3.jpg',497,1,7,1,3),
('TRACTOR - REAR GRADER BLADE', 'These units are ideal for topping and mowing larger sections and;paddocks.',100000,'product-9.jpg',107,1,7,1,3),
('CONCRETE MIXER - PETROL TOWABLE', 'A handy 4-Stroke petrol powered concrete mixer ideal for smaller building projects. Trailer mounted for easy transport to and from site.',100000,'product-12.jpg',99,1,7,2,3),
('CONCRETE MIXER - PETROL', '
A handy 4-Stroke petrol powered concrete mixer ideal for smaller building projects that is mounted on wheels for ease placement on site.',100000,'product-13.jpg',90,1,7,2,3),
('MIXER PUMP 240L DIESEL', '
Larger towable mixer pump with powerful stage 5 diesel motor. Suited to a range of high volume grout, plaster and mortar applications, with aggregate up to 8mm.',100000,'product-14.jpg',90,1,7,2,3),

('LAWN MOWER - ZERO TURN (52IN)', 'A popular self propelled landscaping machine with depth adjustment for harvesting or removing turf. Cuts ready to roll, up to 900sqm of turf per hour.
',100000,'product-19.jpg',323,1,7,3,3),
('LAWN MOWER - ZERO TURN (54IN)', 'A popular self propelled landscaping machine with depth adjustment for harvesting or removing turf. Cuts ready to roll, up to 900sqm of turf per hour.
',100000,'product-20.jpg',294,1,7,3,3),
('LAWN ROTARY TILLER - PETROL', 'Light duty cultivator for establishing garden beds and lawns, ideal for soft or sandy soil. Simple to operate, features a 4-stroke motor.',100000,'product-21.jpg',117,1,7,3,3),
('LAWN TRIMMER MOWER', 'Offset frame allows trimming right up against foundations',100000,'product-22.jpg',115,1,7,3,3),
('CHAINSAW - 300MM (12IN) PETROL', 'Professional 2 stroke chainsaw with a powerful motor suitable for use in remote locations. Ideal for cutting firewood, tree lopping and trimming.',100000,'product-24.jpg',132,1,7,4,3),
('CHAINSAW - 300MM (12IN) CORDLESS', 'Professional 2 stroke chainsaw with a powerful motor suitable for use in remote locations. Ideal for cutting firewood, tree lopping and trimming.',100000,'product-25.jpg',108,1,7,4,3),
('BRISTLE BLASTER - BATTERY', '
The Bristle Blaster combines the ability to produce an abrasive blasted finish with the high mobility and flexibility of a portable hand-held tool.',100000,'product-28.jpg',88,1,7,5,3),
('CHIPPER - 75MM PETROL TOWABLE', '
A fast and efficient, road towable chipper for recycling branches. Turns tree and shrub prunings into mulch or compost. Reduces tree prunings to a manageable size and is capable of chipping branches up to 75mm in diameter.
',100000,'product-29.jpg',231,1,7,5,3),
('GRINDER - ANGLE 225MM', '
A versatile, time saving tool that uses carborundum wheels for; cutting or grinding steel or masonry. Popular applications include light demolition, surface preparation and maintenance, trimming; slate, tiles and pavers.
',100000,'product-30.jpg',64,1,7,5,3),
('GRINDER - ANGLE 115MM TO 125MM', '
A versatile, time saving tool that uses carborundum wheels for; cutting or grinding steel or masonry. Popular applications include light demolition, surface preparation and maintenance, trimming; slate, tiles and pavers.
',100000,'product-31.jpg',46,1,7,5,3),
('TELEHANDLER - 3.8T 8M', '
Extremely versatile telescopic material handling vehicle, for heavy loads, to be transported on all types of terrain.',100000,'product-36.jpg',602,1,7,6,3),


('TRACTOR - 25 HP', 'General purpose tractor with applications that include aerating and topdressing with the appropriate attachments.',100000,'product-1.jpg',305,1,7,1,4),
('MIXER PUMP LARGE DIESEL', 'A large diesel pump with hydraulic worm drive that pumps up to 40m vertically. Suited to thick and free flowing media, with fully controllable delivery flow. Handles wet mortar only with grain size up 6mm and has an adjustable mixing speed.',100000,'product-4.jpg',70,1,7,2,4),
('LAWN DETHATCHER CORDLESS', 'A light-weight battery-powered, cordless scarifier with a 2-in-1 function and easy blade shift. The easily adjusted working depth, together with a powerful engine, efficiently remove matted thatch and moss from the lawn.',100000,'product-5.jpg',114,1,7,3,4),
('CHAINSAW - 450MM (18IN) PETROL', 'Professional 2 stroke chainsaw with a powerful motor suitable for use in remote locations. Ideal for cutting firewood, tree lopping and trimming.
',100000,'product-6.jpg',125,1,7,4,4),
('CHIPPER - 150MM DIESEL', '
A fast and efficient, towable chipper for recycling branches. Turns tree and shrub prunings into mulch or compost. Reduces tree prunings to a manageable size and is capable of chipping branches up to 150 mm in diameter.',100000,'product-7.jpg',367,1,7,5,4),
('TELEHANDLER - 4T 9.5M', '
A versatile lifting solution for construction and industrial projects. With its impressive capacity and reach, it ensures efficient material handling in various work environments.',100000,'product-8.jpg',800,1,7,6,4),
('TRACTOR BROOM - 30HP', 'Road Sweeping unit ideal for road construction/ infrastructure project work.',100000,'product-2.jpg',399,1,7,1,4),
('TRACTOR - REAR GRADER BLADE', 'These units are ideal for topping and mowing larger sections and;paddocks.',100000,'product-9.jpg',107,1,7,1,4),
('CONCRETE MIXER - PETROL TOWABLE', 'A handy 4-Stroke petrol powered concrete mixer ideal for smaller building projects. Trailer mounted for easy transport to and from site.',100000,'product-12.jpg',99,1,7,2,4),
('CONCRETE MIXER - PETROL', '
A handy 4-Stroke petrol powered concrete mixer ideal for smaller building projects that is mounted on wheels for ease placement on site.',100000,'product-13.jpg',90,1,7,2,4),
('LAWN MOWER - ZERO TURN (52IN)', 'A popular self propelled landscaping machine with depth adjustment for harvesting or removing turf. Cuts ready to roll, up to 900sqm of turf per hour.
',100000,'product-19.jpg',323,1,7,3,4),
('LAWN MOWER - ZERO TURN (54IN)', 'A popular self propelled landscaping machine with depth adjustment for harvesting or removing turf. Cuts ready to roll, up to 900sqm of turf per hour.
',100000,'product-20.jpg',294,1,7,3,4),
('CHAINSAW - 300MM (12IN) PETROL', 'Professional 2 stroke chainsaw with a powerful motor suitable for use in remote locations. Ideal for cutting firewood, tree lopping and trimming.',100000,'product-24.jpg',132,1,7,4,4),
('CHAINSAW - 300MM (12IN) CORDLESS', 'Professional 2 stroke chainsaw with a powerful motor suitable for use in remote locations. Ideal for cutting firewood, tree lopping and trimming.',100000,'product-25.jpg',108,1,7,4,4),
('GRINDER - ANGLE 225MM', '
A versatile, time saving tool that uses carborundum wheels for; cutting or grinding steel or masonry. Popular applications include light demolition, surface preparation and maintenance, trimming; slate, tiles and pavers.
',100000,'product-30.jpg',64,1,7,5,4),
('GRINDER - ANGLE 115MM TO 125MM', '
A versatile, time saving tool that uses carborundum wheels for; cutting or grinding steel or masonry. Popular applications include light demolition, surface preparation and maintenance, trimming; slate, tiles and pavers.
',100000,'product-31.jpg',46,1,7,5,4),
('TELEHANDLER - 3.8T 8M', '
Extremely versatile telescopic material handling vehicle, for heavy loads, to be transported on all types of terrain.',100000,'product-36.jpg',602,1,7,6,4),



('TRACTOR - 25 HP', 'General purpose tractor with applications that include aerating and topdressing with the appropriate attachments.',100000,'product-1.jpg',305,1,7,1,5),
('MIXER PUMP LARGE DIESEL', 'A large diesel pump with hydraulic worm drive that pumps up to 40m vertically. Suited to thick and free flowing media, with fully controllable delivery flow. Handles wet mortar only with grain size up 6mm and has an adjustable mixing speed.',100000,'product-4.jpg',70,1,7,2,5),
('LAWN DETHATCHER CORDLESS', 'A light-weight battery-powered, cordless scarifier with a 2-in-1 function and easy blade shift. The easily adjusted working depth, together with a powerful engine, efficiently remove matted thatch and moss from the lawn.',100000,'product-5.jpg',114,1,7,3,5),
('CHAINSAW - 450MM (18IN) PETROL', 'Professional 2 stroke chainsaw with a powerful motor suitable for use in remote locations. Ideal for cutting firewood, tree lopping and trimming.
',100000,'product-6.jpg',125,1,7,4,5),
('CHIPPER - 150MM DIESEL', '
A fast and efficient, towable chipper for recycling branches. Turns tree and shrub prunings into mulch or compost. Reduces tree prunings to a manageable size and is capable of chipping branches up to 150 mm in diameter.',100000,'product-7.jpg',367,1,7,5,5),
('TELEHANDLER - 4T 9.5M', '
A versatile lifting solution for construction and industrial projects. With its impressive capacity and reach, it ensures efficient material handling in various work environments.',100000,'product-8.jpg',800,1,7,6,5),

('TRACTOR BROOM - 30HP', 'Road Sweeping unit ideal for road construction/ infrastructure project work.',100000,'product-2.jpg',399,1,7,1,5),

('CONCRETE MIXER - PETROL TOWABLE', 'A handy 4-Stroke petrol powered concrete mixer ideal for smaller building projects. Trailer mounted for easy transport to and from site.',100000,'product-12.jpg',99,1,7,2,5),

('LAWN MOWER - ZERO TURN (52IN)', 'A popular self propelled landscaping machine with depth adjustment for harvesting or removing turf. Cuts ready to roll, up to 900sqm of turf per hour.
',100000,'product-19.jpg',323,1,7,3,5),
('LAWN MOWER - ZERO TURN (54IN)', 'A popular self propelled landscaping machine with depth adjustment for harvesting or removing turf. Cuts ready to roll, up to 900sqm of turf per hour.
',100000,'product-20.jpg',294,1,7,3,5),
('CHAINSAW - 300MM (12IN) PETROL', 'Professional 2 stroke chainsaw with a powerful motor suitable for use in remote locations. Ideal for cutting firewood, tree lopping and trimming.',100000,'product-24.jpg',132,1,7,4,5),
('CHAINSAW - 300MM (12IN) CORDLESS', 'Professional 2 stroke chainsaw with a powerful motor suitable for use in remote locations. Ideal for cutting firewood, tree lopping and trimming.',100000,'product-25.jpg',108,1,7,4,5),

('GRINDER - ANGLE 115MM TO 125MM', '
A versatile, time saving tool that uses carborundum wheels for; cutting or grinding steel or masonry. Popular applications include light demolition, surface preparation and maintenance, trimming; slate, tiles and pavers.
',100000,'product-31.jpg',46,1,7,5,5),
('TELEHANDLER - 3.8T 8M', '
Extremely versatile telescopic material handling vehicle, for heavy loads, to be transported on all types of terrain.',100000,'product-36.jpg',602,1,7,6,5),




('TRACTOR - 25 HP', 'General purpose tractor with applications that include aerating and topdressing with the appropriate attachments.',100000,'product-1.jpg',305,1,7,1,6),
('MIXER PUMP LARGE DIESEL', 'A large diesel pump with hydraulic worm drive that pumps up to 40m vertically. Suited to thick and free flowing media, with fully controllable delivery flow. Handles wet mortar only with grain size up 6mm and has an adjustable mixing speed.',100000,'product-4.jpg',70,1,7,2,6),
('LAWN DETHATCHER CORDLESS', 'A light-weight battery-powered, cordless scarifier with a 2-in-1 function and easy blade shift. The easily adjusted working depth, together with a powerful engine, efficiently remove matted thatch and moss from the lawn.',100000,'product-5.jpg',114,1,7,3,6),
('CHAINSAW - 450MM (18IN) PETROL', 'Professional 2 stroke chainsaw with a powerful motor suitable for use in remote locations. Ideal for cutting firewood, tree lopping and trimming.
',100000,'product-6.jpg',125,1,7,4,6),
('CHIPPER - 150MM DIESEL', '
A fast and efficient, towable chipper for recycling branches. Turns tree and shrub prunings into mulch or compost. Reduces tree prunings to a manageable size and is capable of chipping branches up to 150 mm in diameter.',100000,'product-7.jpg',367,1,7,5,6),
('TELEHANDLER - 4T 9.5M', '
A versatile lifting solution for construction and industrial projects. With its impressive capacity and reach, it ensures efficient material handling in various work environments.',100000,'product-8.jpg',800,1,7,6,6),

('TRACTOR BROOM - 30HP', 'Road Sweeping unit ideal for road construction/ infrastructure project work.',100000,'product-2.jpg',399,1,7,1,6),

('CONCRETE MIXER - PETROL TOWABLE', 'A handy 4-Stroke petrol powered concrete mixer ideal for smaller building projects. Trailer mounted for easy transport to and from site.',100000,'product-12.jpg',99,1,7,2,6),

('LAWN MOWER - ZERO TURN (52IN)', 'A popular self propelled landscaping machine with depth adjustment for harvesting or removing turf. Cuts ready to roll, up to 900sqm of turf per hour.
',100000,'product-19.jpg',323,1,7,3,6),
('LAWN MOWER - ZERO TURN (54IN)', 'A popular self propelled landscaping machine with depth adjustment for harvesting or removing turf. Cuts ready to roll, up to 900sqm of turf per hour.
',100000,'product-20.jpg',294,1,7,3,6),
('CHAINSAW - 300MM (12IN) PETROL', 'Professional 2 stroke chainsaw with a powerful motor suitable for use in remote locations. Ideal for cutting firewood, tree lopping and trimming.',100000,'product-24.jpg',132,1,7,4,6),
('CHAINSAW - 300MM (12IN) CORDLESS', 'Professional 2 stroke chainsaw with a powerful motor suitable for use in remote locations. Ideal for cutting firewood, tree lopping and trimming.',100000,'product-25.jpg',108,1,7,4,6),

('GRINDER - ANGLE 115MM TO 125MM', '
A versatile, time saving tool that uses carborundum wheels for; cutting or grinding steel or masonry. Popular applications include light demolition, surface preparation and maintenance, trimming; slate, tiles and pavers.
',100000,'product-31.jpg',46,1,7,5,6),
('TELEHANDLER - 3.8T 8M', '
Extremely versatile telescopic material handling vehicle, for heavy loads, to be transported on all types of terrain.',100000,'product-36.jpg',602,1,7,6,6)

;

ALTER TABLE inventory AUTO_INCREMENT = 10001;

INSERT INTO inventory (store_id,equipment_id,purchase_date,status) Values
(1,1,'2024-01-01','available'),
(1,2,'2024-01-01','available'),
(1,3,'2024-01-01','available'),
(1,4,'2024-01-01','available'),
(1,5,'2024-01-01','available'),
(1,6,'2024-01-01','available'),
(1,6,'2024-01-01','available'),
(1,6,'2024-01-01','available'),
(1,7,'2024-01-01','available'),
(1,7,'2024-01-01','available'),
(1,8,'2024-01-01','available'),
(1,8,'2024-01-01','available'),
(1,9,'2024-01-01','available'),
(1,9,'2024-01-01','available'),
(1,10,'2024-01-01','available'),
(1,10,'2024-01-01','available'),
(1,10,'2024-01-01','available'),
(1,11,'2024-01-01','available'),
(1,11,'2024-01-01','available'),
(1,11,'2024-01-01','available'),
(1,12,'2024-01-01','available'),
(1,12,'2024-01-01','available'),
(1,12,'2024-01-01','available'),
(1,13,'2024-01-01','available'),
(1,13,'2024-01-01','available'),
(1,13,'2024-01-01','available'),
(1,14,'2024-01-01','available'),
(1,14,'2024-01-01','available'),
(1,14,'2024-01-01','available'),
(1,15,'2024-01-01','available'),
(1,15,'2024-01-01','available'),
(1,15,'2024-01-01','available'),
(1,16,'2024-01-01','available'),
(1,16,'2024-01-01','available'),
(1,17,'2024-01-01','available'),
(1,17,'2024-01-01','available'),
(1,18,'2024-01-01','available'),
(1,18,'2024-01-01','available'),
(1,19,'2024-01-01','available'),
(1,19,'2024-01-01','available'),
(1,19,'2024-01-01','available'),
(1,20,'2024-01-01','available'),
(1,20,'2024-01-01','available'),
(1,20,'2024-01-01','available'),
(1,21,'2024-01-01','available'),
(1,21,'2024-01-01','available'),
(1,22,'2024-01-01','available'),
(1,22,'2024-01-01','available'),
(1,23,'2024-01-01','available'),
(1,23,'2024-01-01','available'),
(1,24,'2024-01-01','available'),
(1,25,'2024-01-01','available'),
(1,26,'2024-01-01','available'),
(1,27,'2024-01-01','available'),
(1,27,'2024-01-01','available'),
(1,27,'2024-01-01','available'),
(1,28,'2024-01-01','available'),
(1,29,'2024-01-01','available'),
(1,29,'2024-01-01','available'),
(1,29,'2024-01-01','available'),
(1,30,'2024-01-01','available'),
(1,30,'2024-01-01','available'),
(1,30,'2024-01-01','available'),
(1,31,'2024-01-01','available'),
(1,31,'2024-01-01','available'),
(1,31,'2024-01-01','available'),
(1,32,'2024-01-01','available'),
(1,33,'2024-01-01','available'),
(1,34,'2024-01-01','available'),
(1,35,'2024-01-01','available'),
(1,36,'2024-01-01','available'),
(2,37,'2024-01-01','available'),
(2,38,'2024-01-01','available'),
(2,39,'2024-01-01','available'),
(2,40,'2024-01-01','available'),
(2,41,'2024-01-01','available'),
(2,42,'2024-01-01','available'),
(2,43,'2024-01-01','available'),
(2,44,'2024-01-01','available'),
(2,45,'2024-01-01','available'),
(2,46,'2024-01-01','available'),
(2,46,'2024-01-01','available'),
(2,47,'2024-01-01','available'),
(2,47,'2024-01-01','available'),
(2,48,'2024-01-01','available'),
(2,48,'2024-01-01','available'),
(2,49,'2024-01-01','available'),
(2,49,'2024-01-01','available'),
(2,50,'2024-01-01','available'),
(2,50,'2024-01-01','available'),
(2,51,'2024-01-01','available'),
(2,51,'2024-01-01','available'),
(2,52,'2024-01-01','available'),
(2,52,'2024-01-01','available'),
(2,53,'2024-01-01','available'),
(2,53,'2024-01-01','available'),
(2,54,'2024-01-01','available'),
(2,54,'2024-01-01','available'),
(2,55,'2024-01-01','available'),
(2,56,'2024-01-01','available'),
(2,57,'2024-01-01','available'),
(2,58,'2024-01-01','available'),
(2,59,'2024-01-01','available'),
(3,60,'2024-01-01','available'),
(3,61,'2024-01-01','available'),
(3,62,'2024-01-01','available'),
(3,63,'2024-01-01','available'),
(3,64,'2024-01-01','available'),
(3,65,'2024-01-01','available'),
(3,66,'2024-01-01','available'),
(3,67,'2024-01-01','available'),
(3,68,'2024-01-01','available'),
(3,69,'2024-01-01','available'),
(3,70,'2024-01-01','available'),
(3,71,'2024-01-01','available'),
(3,72,'2024-01-01','available'),
(3,73,'2024-01-01','available'),
(3,74,'2024-01-01','available'),
(3,75,'2024-01-01','available'),
(3,76,'2024-01-01','available'),
(3,77,'2024-01-01','available'),
(3,78,'2024-01-01','available'),
(3,79,'2024-01-01','available'),
(3,80,'2024-01-01','available'),
(3,81,'2024-01-01','available'),
(3,82,'2024-01-01','available'),
(4,83,'2024-01-01','available'),
(4,84,'2024-01-01','available'),
(4,85,'2024-01-01','available'),
(4,86,'2024-01-01','available'),
(4,87,'2024-01-01','available'),
(4,88,'2024-01-01','available'),
(4,89,'2024-01-01','available'),
(4,90,'2024-01-01','available'),
(4,91,'2024-01-01','available'),
(4,92,'2024-01-01','available'),
(4,93,'2024-01-01','available'),
(4,94,'2024-01-01','available'),
(4,95,'2024-01-01','available'),
(4,96,'2024-01-01','available'),
(4,97,'2024-01-01','available'),
(4,98,'2024-01-01','available'),
(4,99,'2024-01-01','available'),
(5,100,'2024-01-01','available'),
(5,101,'2024-01-01','available'),
(5,102,'2024-01-01','available'),
(5,103,'2024-01-01','available'),
(5,104,'2024-01-01','available'),
(5,105,'2024-01-01','available'),
(5,106,'2024-01-01','available'),
(5,107,'2024-01-01','available'),
(5,108,'2024-01-01','available'),
(5,109,'2024-01-01','available'),
(5,110,'2024-01-01','available'),
(5,111,'2024-01-01','available'),
(5,112,'2024-01-01','available'),
(5,113,'2024-01-01','available'),
(6,114,'2024-01-01','available'),
(6,115,'2024-01-01','available'),
(6,116,'2024-01-01','available'),
(6,117,'2024-01-01','available'),
(6,118,'2024-01-01','available'),
(6,119,'2024-01-01','available'),
(6,120,'2024-01-01','available'),
(6,121,'2024-01-01','available'),
(6,122,'2024-01-01','available'),
(6,123,'2024-01-01','available'),
(6,124,'2024-01-01','available'),
(6,125,'2024-01-01','available'),
(6,126,'2024-01-01','available'),
(6,127,'2024-01-01','available')
;

INSERT INTO booking (customer_id,store_id,total_amount, booking_date,status) Values
(1,1,375,'2024-05-01','paid'),
(1,1,375,'2024-05-25','paid'),
(1,1,375,'2024-05-25','paid'); 


INSERT INTO booking_detail (booking_id,equipment_id,start_date, end_date,total,quantity) Values					
(1,1,'2024-06-09','2024-06-10',305,1),
(1,6,'2024-06-08','2024-05-09',70,1),
(2,2,'2024-06-11','2024-06-12',1596,1),  
(2,6,'2024-06-14','2024-06-15',140,1),
(3,1,'2024-06-14','2024-06-16',305,1),
(3,6,'2024-06-12','2024-06-13',70,1);

INSERT INTO payment (booking_id,amount,payment_date, status) Values					
(1,375,'2024-05-01','successful'),
(2,1736,'2024-05-25','successful'),
(3,375,'2024-05-25','successful');

INSERT INTO in_out_record (detail_id,pickup_time,return_time) Values					
(1,'2024-06-09','2024-06-10'),
(2,'2024-06-08','2024-06-09'),
(3,null,null),
(4,null,null),
(5,null,null),
(6,null,null);



INSERT INTO promotion (promotion_name,description,start_day, end_day,discount_rate,store_id) Values					
('ABC',"King'S Birthday Celebration",'2024-06-01','2024-06-30',10,1),
('QWE',"Mid Season Sale",'2024-06-15','2024-06-30',15,2),
('ZXC',"Black Friday Sale",'2024-11-29','2024-12-01',30,3),
('ABC',"King'S Birthday Celebration",'2024-06-01','2024-06-03',10,4),
('ABC',"King'S Birthday Celebration",'2024-06-01','2024-06-10',10,5),
('QWE',"Mid Season Sale",'2024-06-15','2024-06-30',15,6),
('ZXC',"Black Friday Sale",'2024-11-29','2024-12-01',30,1);

INSERT INTO news (title,content,store_id) Values		
('Auckland Store Temporarily Closes',"We regret to inform you that due to unforeseen circumstances, the Auckland store will be closed this upcoming Monday. We apologize for any inconvenience this temporary closure may cause.
Rest assured, we are working diligently to resolve the situation and ensure that our services return to normal as soon as possible. Your understanding and patience during this time are greatly appreciated.",1),
('Big Sales in Wellington Store',"We are thrilled to share some exciting news with you! This weekend, our Wellington Store is hosting a spectacular sale event just for our valued members. Get ready to enjoy incredible discounts on a wide range of products.
Don't miss out on this fantastic opportunity to shop and save! Visit us at the Wellington Store this weekend and take advantage of these exclusive deals.",2),
('Month Sales Review',"This month, our sales have shown remarkable growth. We hit a new record with a 15% increase compared to last month. Thank you for your hard work and dedication. Keep up the great work!.",Null);







