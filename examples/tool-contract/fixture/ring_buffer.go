package ringbuf

import "errors"

// Buffer is a fixed-capacity FIFO ring of integers.
type Buffer struct {
	items []int
	head  int
	count int
}

// ErrFull is returned by Push when the buffer has no free slot.
var ErrFull = errors.New("ring buffer is full")

// ErrEmpty is returned by Pop when the buffer holds no items.
var ErrEmpty = errors.New("ring buffer is empty")

// New returns a buffer that holds up to capacity items.
func New(capacity int) *Buffer {
	if capacity < 1 {
		capacity = 1
	}
	return &Buffer{items: make([]int, capacity)}
}

// Len reports how many items are stored.
func (b *Buffer) Len() int {
	return b.count
}

// Cap reports the fixed capacity.
func (b *Buffer) Cap() int {
	return len(b.items)
}

// Push appends v to the tail. It fails with ErrFull rather than overwriting.
func (b *Buffer) Push(v int) error {
	if b.count == len(b.items) {
		return ErrFull
	}
	tail := (b.head + b.count) % len(b.items)
	b.items[tail] = v
	b.count++
	return nil
}

// Pop removes and returns the oldest item.
func (b *Buffer) Pop() (int, error) {
	if b.count == 0 {
		return 0, ErrEmpty
	}
	v := b.items[b.head]
	b.head = (b.head + 1) % len(b.items)
	b.count--
	return v, nil
}

// Peek returns the oldest item without removing it.
func (b *Buffer) Peek() (int, error) {
	if b.count == 0 {
		return 0, ErrEmpty
	}
	return b.items[b.head], nil
}

// Drain removes every item and returns them oldest first.
func (b *Buffer) Drain() []int {
	out := make([]int, 0, b.count)
	for b.count > 0 {
		v, _ := b.Pop()
		out = append(out, v)
	}
	return out
}

// Reset empties the buffer without changing its capacity.
func (b *Buffer) Reset() {
	b.head = 0
	b.count = 0
}

// Snapshot returns a copy of the stored items, oldest first, without changing the buffer.
func (b *Buffer) Snapshot() []int {
	out := make([]int, b.count)
	for i := 0; i < b.count; i++ {
		out[i] = b.items[(b.head+i)%len(b.items)]
	}
	return out
}

// Full reports whether the next Push would fail.
func (b *Buffer) Full() bool {
	return b.count == len(b.items)
}

// Empty reports whether the buffer holds no items.
func (b *Buffer) Empty() bool {
	return b.count == 0
}

// Grow increases capacity by n slots, keeping the stored items in order.
func (b *Buffer) Grow(n int) {
	if n <= 0 {
		return
	}
	next := make([]int, len(b.items)+n)
	for i := 0; i < b.count; i++ {
		next[i] = b.items[(b.head+i)%len(b.items)]
	}
	b.items = next
	b.head = 0
}

// Shrink reduces capacity by n slots. It fails with ErrFull if the stored items would not fit.
func (b *Buffer) Shrink(n int) error {
	if n <= 0 {
		return nil
	}
	newCap := len(b.items) - n
	if newCap < 1 {
		newCap = 1
	}
	if b.count > newCap {
		return ErrFull
	}
	next := make([]int, newCap)
	for i := 0; i < b.count; i++ {
		next[i] = b.items[(b.head+i)%len(b.items)]
	}
	b.items = next
	b.head = 0
	return nil
}

// PushAll pushes each value in order, stopping at the first failure.
func (b *Buffer) PushAll(values []int) (int, error) {
	pushed := 0
	for _, v := range values {
		if err := b.Push(v); err != nil {
			return pushed, err
		}
		pushed++
	}
	return pushed, nil
}

// MaxStored returns the largest stored value. It reports ErrEmpty when nothing is stored.
func (b *Buffer) MaxStored() (int, error) {
	if b.count == 0 {
		return 0, ErrEmpty
	}
	best := b.items[b.head]
	for _, v := range b.Snapshot() {
		if v > best {
			best = v
		}
	}
	return best, nil
}

// Sum returns the total of all stored values.
func (b *Buffer) Sum() int {
	total := 0
	for _, v := range b.Snapshot() {
		total += v
	}
	return total
}

// Average returns the mean of stored values as a float. It returns 0 when empty.
func (b *Buffer) Average() float64 {
	if b.count == 0 {
		return 0
	}
	return float64(b.Sum()) / float64(b.count)
}

// Contains reports whether v is stored.
func (b *Buffer) Contains(v int) bool {
	for _, x := range b.Snapshot() {
		if x == v {
			return true
		}
	}
	return false
}

// IndexOf returns the position of v counted from the oldest item, or -1 if absent.
func (b *Buffer) IndexOf(v int) int {
	for i, x := range b.Snapshot() {
		if x == v {
			return i
		}
	}
	return -1
}

// RotateLeft moves the oldest item to the tail, n times.
func (b *Buffer) RotateLeft(n int) {
	if b.count == 0 {
		return
	}
	for i := 0; i < n%b.count; i++ {
		v, _ := b.Pop()
		_ = b.Push(v)
	}
}
