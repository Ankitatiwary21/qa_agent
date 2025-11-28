# E-Shop Checkout - Product Specifications

## 1. Product Catalog

### Available Products
| Product ID | Name | Price |
|------------|------|-------|
| PROD-001 | Wireless Headphones | $79.99 |
| PROD-002 | USB-C Cable | $12.99 |
| PROD-003 | Phone Stand | $24.99 |

### Cart Rules
- Users can add multiple quantities of the same item
- Maximum quantity per item: 99
- Minimum quantity: 1
- Cart updates automatically when quantity changes
- Total price = Sum of (item price × quantity) for all items

## 2. Discount Code System

### Valid Discount Codes
| Code | Discount | Description |
|------|----------|-------------|
| SAVE15 | 15% off | Standard discount code |
| WELCOME10 | 10% off | New customer discount |
| FREESHIP | Free shipping | Waives shipping cost |

### Discount Rules
- Only ONE discount code can be applied per order
- Discount is applied to subtotal BEFORE shipping
- Invalid codes must display error: "Invalid discount code"
- Empty code submission should show: "Please enter a discount code"
- Discount codes are case-insensitive (SAVE15 = save15)

## 3. Shipping Options

### Available Methods
| Method | Cost | Delivery Time |
|--------|------|---------------|
| Standard Shipping | Free | 5-7 business days |
| Express Shipping | $10.00 | 1-2 business days |

### Shipping Rules
- Default selection: Standard Shipping
- Shipping cost is added AFTER discount is applied
- User must select a shipping method before checkout

## 4. Payment Methods

### Supported Payment Options
- Credit Card
- PayPal

### Payment Rules
- User must select a payment method
- Default: No payment method selected
- Credit Card: No additional validation in this demo
- PayPal: No additional validation in this demo

## 5. Order Submission

### Success Criteria
- All required fields filled correctly
- Valid email format
- Shipping method selected
- Payment method selected
- At least one item in cart

### Success Message
- Display: "Payment Successful! Your order has been placed."

### Failure Handling
- Display specific error messages for each validation failure