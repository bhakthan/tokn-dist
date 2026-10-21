package shop

// SumItems looks up the price of every item in a comma-separated list.
func SumItems(raw string) int {
	total := 0
	for _, name := range ParseItems(raw) {
		total += LookupPrice(name)
	}
	return total
}

// ParseItems splits the raw order line into item names.
func ParseItems(raw string) []string {
	return splitOn(raw, ',')
}

// splitOn splits s on sep. It is a leaf helper.
func splitOn(s string, sep byte) []string {
	var parts []string
	start := 0
	for i := 0; i < len(s); i++ {
		if s[i] == sep {
			parts = append(parts, s[start:i])
			start = i + 1
		}
	}
	return append(parts, s[start:])
}
