package shop

// FormatReceipt renders the receipt text for a total.
func FormatReceipt(total int) string {
	if total < 0 {
		return renderLine("invalid")
	}
	return renderLine("total")
}

// ExportReport writes the receipt for a total to the report format.
func ExportReport(total int) string {
	return FormatReceipt(total)
}

// renderLine formats one labelled line. It is a leaf.
func renderLine(label string) string {
	return "[" + label + "]"
}
