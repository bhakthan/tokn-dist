package shop

var prices = map[string]int{
	"apple": 3,
	"bread": 5,
	"milk":  4,
}

// LookupPrice returns the unit price of a catalog item. It is a leaf.
func LookupPrice(name string) int {
	return prices[name]
}
