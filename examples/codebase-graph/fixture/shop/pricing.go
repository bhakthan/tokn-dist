package shop

// ComputeTotal sums the line items and applies any discount.
func ComputeTotal(raw string) int {
	sum := SumItems(raw)
	return ApplyDiscount(sum)
}
