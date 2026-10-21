package shop

// HandleCheckout is the entry point for a checkout request.
func HandleCheckout(raw string) string {
	total := ComputeTotal(raw)
	return FormatReceipt(total)
}
