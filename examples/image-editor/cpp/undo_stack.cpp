// Command-pattern undo/redo for pixel edits, storing only the touched rectangle.
// Build: g++ -std=c++17 -O2 undo_stack.cpp -o undo_stack && ./undo_stack

#include <cassert>
#include <cstdint>
#include <cstdio>
#include <memory>
#include <vector>

struct Canvas {
  int w, h;
  std::vector<uint8_t> px;  // one grey byte per pixel keeps the example small
  Canvas(int w_, int h_) : w(w_), h(h_), px(static_cast<size_t>(w_) * h_, 0) {}
  uint8_t& at(int x, int y) { return px[static_cast<size_t>(y) * w + x]; }
};

struct Command {
  virtual ~Command() = default;
  virtual void apply(Canvas& c) = 0;
  virtual void revert(Canvas& c) = 0;
};

// Fill a rectangle; remembers the previous pixels of that rectangle only.
class FillRect : public Command {
  int x0_, y0_, x1_, y1_;
  uint8_t value_;
  std::vector<uint8_t> before_;

 public:
  FillRect(int x0, int y0, int x1, int y1, uint8_t v) : x0_(x0), y0_(y0), x1_(x1), y1_(y1), value_(v) {}
  void apply(Canvas& c) override {
    before_.clear();
    for (int y = y0_; y < y1_; ++y)
      for (int x = x0_; x < x1_; ++x) {
        before_.push_back(c.at(x, y));
        c.at(x, y) = value_;
      }
  }
  void revert(Canvas& c) override {
    size_t i = 0;
    for (int y = y0_; y < y1_; ++y)
      for (int x = x0_; x < x1_; ++x) c.at(x, y) = before_[i++];
  }
};

class History {
  Canvas& canvas_;
  std::vector<std::unique_ptr<Command>> undo_, redo_;  // unique_ptr: history owns its commands

 public:
  explicit History(Canvas& c) : canvas_(c) {}
  void execute(std::unique_ptr<Command> cmd) {
    cmd->apply(canvas_);
    undo_.push_back(std::move(cmd));
    redo_.clear();  // a new edit discards the redo branch
  }
  bool undo() {
    if (undo_.empty()) return false;
    undo_.back()->revert(canvas_);
    redo_.push_back(std::move(undo_.back()));
    undo_.pop_back();
    return true;
  }
  bool redo() {
    if (redo_.empty()) return false;
    redo_.back()->apply(canvas_);
    undo_.push_back(std::move(redo_.back()));
    redo_.pop_back();
    return true;
  }
};

int main() {
  Canvas canvas(8, 8);
  History h(canvas);
  h.execute(std::make_unique<FillRect>(0, 0, 4, 4, 200));
  h.execute(std::make_unique<FillRect>(2, 2, 6, 6, 50));
  assert(canvas.at(3, 3) == 50 && canvas.at(1, 1) == 200);

  h.undo();
  assert(canvas.at(3, 3) == 200 && canvas.at(5, 5) == 0);  // overlap restored to the first fill
  h.redo();
  assert(canvas.at(3, 3) == 50);
  h.undo();
  h.undo();
  assert(canvas.at(1, 1) == 0 && !h.undo());

  h.redo();
  h.execute(std::make_unique<FillRect>(0, 0, 1, 1, 9));
  assert(!h.redo());  // redo branch was discarded
  std::puts("undo_stack: all checks passed");
}
