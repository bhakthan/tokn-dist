package shop

// ApplyDiscount takes 10% off large orders.
func ApplyDiscount(amount int) int {
	if IsBulk(amount) {
		return amount * 9 / 10
	}
	return amount
}

// IsBulk reports whether an order is large enough for a discount. It is a leaf.
func IsBulk(amount int) bool {
	return amount >= 100
}
