-- ============================================================================
-- 茶饮销售数据分析看板 —— 数据库建表脚本
-- 数据库: MySQL 8.0+
-- 作用  : 创建 category(商品品类)、product(商品)、orders(订单明细) 三张表
--         通过外键关联实现多表 JOIN；orders 表按 (order_id, product_id)
--         作为复合主键，一张订单可含多个商品，便于用 COUNT(DISTINCT order_id)
--         统计订单量、用窗口函数做排名/占比分析。
-- 执行  : mysql -u root -p < create_tables.sql
-- ============================================================================

-- 建库（若已存在则保留，避免误删数据）
CREATE DATABASE IF NOT EXISTS tea_sales
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_general_ci;

USE tea_sales;

-- ----------------------------------------------------------------------------
-- 表1: category —— 商品品类表（维度表）
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS product;
DROP TABLE IF EXISTS category;

CREATE TABLE category (
    category_id   INT          NOT NULL AUTO_INCREMENT COMMENT '品类ID(主键)',
    category_name VARCHAR(50)  NOT NULL COMMENT '品类名称',
    description   VARCHAR(200) DEFAULT NULL COMMENT '品类描述',
    PRIMARY KEY (category_id),
    UNIQUE KEY uk_category_name (category_name)
) ENGINE=InnoDB COMMENT='商品品类维度表';

-- ----------------------------------------------------------------------------
-- 表2: product —— 商品表（维度表，外键关联 category）
-- ----------------------------------------------------------------------------
CREATE TABLE product (
    product_id   INT          NOT NULL AUTO_INCREMENT COMMENT '商品ID(主键)',
    product_name VARCHAR(100) NOT NULL COMMENT '商品名称',
    category_id  INT          NOT NULL COMMENT '所属品类ID(外键)',
    base_price   DECIMAL(8,2) NOT NULL COMMENT '标准售价(元)',
    PRIMARY KEY (product_id),
    KEY idx_product_category (category_id),
    CONSTRAINT fk_product_category FOREIGN KEY (category_id)
        REFERENCES category (category_id)
) ENGINE=InnoDB COMMENT='商品维度表';

-- ----------------------------------------------------------------------------
-- 表3: orders —— 订单明细表（事实表，外键关联 product）
--       复合主键 (order_id, product_id)：同一订单可包含多个商品 SKU
-- ----------------------------------------------------------------------------
CREATE TABLE orders (
    order_id     BIGINT        NOT NULL COMMENT '订单号(同一订单多商品时重复)',
    order_date   DATE          NOT NULL COMMENT '下单日期',
    city         VARCHAR(50)   NOT NULL COMMENT '城市',
    season       VARCHAR(20)   DEFAULT NULL COMMENT '季节(春/夏/秋/冬)',
    is_holiday   TINYINT       NOT NULL DEFAULT 0 COMMENT '是否节假日 1是/0否',
    discount_rate DECIMAL(4,2) NOT NULL DEFAULT 0.00 COMMENT '折扣率 0~1(如0.15为85折)',
    product_id   INT           NOT NULL COMMENT '商品ID(外键)',
    quantity     INT           NOT NULL COMMENT '购买数量',
    unit_price   DECIMAL(8,2)  NOT NULL COMMENT '成交单价(元，已含折扣)',
    amount       DECIMAL(10,2) NOT NULL COMMENT '该行小计金额 = quantity * unit_price',
    PRIMARY KEY (order_id, product_id),
    KEY idx_orders_date (order_date),
    KEY idx_orders_city (city),
    KEY idx_orders_product (product_id),
    KEY idx_orders_holiday (is_holiday, discount_rate),
    CONSTRAINT fk_orders_product FOREIGN KEY (product_id)
        REFERENCES product (product_id)
) ENGINE=InnoDB COMMENT='订单明细事实表';
