// Simple Union-Find implementation
export default class UnionFind {
  private parent: Map<string, string>;
  private rank: Map<string, number>;

  constructor(elements: string[]) {
    this.parent = new Map(elements.map((e) => [e, e]));
    this.rank = new Map(elements.map((e) => [e, 0]));
  }

  find(x: string): string {
    if (this.parent.get(x) !== x) {
      this.parent.set(x, this.find(this.parent.get(x)!)); // Path compression
    }
    return this.parent.get(x)!;
  }

  union(x: string, y: string): void {
    const rootX = this.find(x);
    const rootY = this.find(y);

    if (rootX !== rootY) {
      const rankX = this.rank.get(rootX)!;
      const rankY = this.rank.get(rootY)!;

      if (rankX > rankY) {
        this.parent.set(rootY, rootX);
      } else if (rankX < rankY) {
        this.parent.set(rootX, rootY);
      } else {
        this.parent.set(rootY, rootX);
        this.rank.set(rootX, rankX + 1);
      }
    }
  }
}