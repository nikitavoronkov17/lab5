"""
Лабораторная работа № 5. Вариант 5.
Хеш-таблица: метод цепочек и линейное пробирование.
Ключи — целые, кратные 10; n = 25 000; m = 32 771 (простое).
Хеш-функция — метод деления: h(k) = k mod m.
Доп. задание В5 — сравнение с встроенным dict.

Всё в одном файле: две реализации хеш-таблицы, замер, эксперимент,
графики. Внешняя зависимость — только matplotlib.
"""
import math
import random
import time


M = 32_771          # размер таблицы (простое число)
N = 25_000          # число ключей
K_MULT = 10         # ключи кратны 10
K_QUERIES = 10_000  # число запросов на поиск


# ==================== Метод цепочек ====================

class ChainHashTable:
    """Хеш-таблица с разрешением коллизий методом цепочек."""

    def __init__(self, m=M):
        self.m = m
        self.slots = [[] for _ in range(m)]
        self.n = 0
        self.probes = 0          # счётчик просмотренных элементов

    def _hash(self, key):
        return key % self.m

    def insert(self, key, value):
        chain = self.slots[self._hash(key)]
        for i, (k, _) in enumerate(chain):
            self.probes += 1
            if k == key:
                chain[i] = (key, value)
                return
        chain.append((key, value))
        self.n += 1

    def search(self, key):
        for k, v in self.slots[self._hash(key)]:
            self.probes += 1
            if k == key:
                return v
        return None

    def chain_lengths(self):
        return [len(c) for c in self.slots]

    def __len__(self):
        return self.n


# ==================== Открытая адресация: линейное пробирование ====================

class OpenHashTable:
    """Хеш-таблица с открытой адресацией (линейное пробирование)."""

    EMPTY = object()
    DELETED = object()

    def __init__(self, m=M):
        self.m = m
        self.keys = [self.EMPTY] * m
        self.values = [None] * m
        self.n = 0
        self.probes = 0

    def _hash(self, key):
        return key % self.m

    def insert(self, key, value):
        pos = self._hash(key)
        for _ in range(self.m):
            self.probes += 1
            k = self.keys[pos]
            if k is self.EMPTY or k is self.DELETED:
                self.keys[pos], self.values[pos] = key, value
                self.n += 1
                return
            if k == key:
                self.values[pos] = value
                return
            pos = (pos + 1) % self.m
        raise RuntimeError("Таблица переполнена")

    def search(self, key):
        pos = self._hash(key)
        for _ in range(self.m):
            self.probes += 1
            k = self.keys[pos]
            if k is self.EMPTY:
                return None
            if k != self.DELETED and k == key:
                return self.values[pos]
            pos = (pos + 1) % self.m
        return None

    def cluster_lengths(self):
        """Длины непрерывных занятых участков."""
        occupied = [k is not self.EMPTY for k in self.keys]
        lengths, current = [], 0
        for flag in occupied + [False]:
            if flag:
                current += 1
            elif current:
                lengths.append(current)
                current = 0
        return lengths

    def __len__(self):
        return self.n


# ==================== Замер ====================

def benchmark(table, keys, queries):
    """Возвращает (время вставки, время поиска, среднее число проб при поиске)."""
    t0 = time.perf_counter()
    for k in keys:
        table.insert(k, k)
    t_insert = time.perf_counter() - t0

    table.probes = 0
    t0 = time.perf_counter()
    for q in queries:
        table.search(q)
    t_search = time.perf_counter() - t0
    return t_insert, t_search, table.probes / len(queries)


# ==================== Эксперимент ====================

if __name__ == "__main__":
    import matplotlib.pyplot as plt

    rng = random.Random(42)

    # Ключи, кратные 10, из диапазона, чтобы не пересекаться с m
    keys = [K_MULT * rng.randrange(1, 10_000_000) for _ in range(N)]
    keys = list(dict.fromkeys(keys))          # убрать возможные дубли
    N = len(keys)
    queries = [rng.choice(keys) for _ in range(K_QUERIES)]

    alpha = N / M
    print(f"Вариант 5: n = {N}, m = {M}, α = {alpha:.4f}")
    print(f"Ключи кратны {K_MULT}; gcd({K_MULT}, {M}) = "
          f"{math.gcd(K_MULT, M)}\n")

    results = {}
    for name, table in [("Цепочки", ChainHashTable()),
                        ("Линейное пробирование", OpenHashTable())]:
        ti, ts, probes = benchmark(table, keys, queries)
        results[name] = (ti, ts, probes)
        print(f"{name:<24} вставка {ti:.4f} с, поиск {ts:.4f} с, "
              f"проб на запрос {probes:.2f}")

    # --- В5: сравнение с dict ---
    print("\n--- В5: сравнение с dict ---")
    t0 = time.perf_counter()
    d = {k: k for k in keys}
    ti = time.perf_counter() - t0
    t0 = time.perf_counter()
    for q in queries:
        d.get(q)
    ts = time.perf_counter() - t0
    print(f"{'dict (эталон)':<24} вставка {ti:.4f} с, поиск {ts:.4f} с")

    # --- Распределение длин цепочек ---
    ch = ChainHashTable()
    for k in keys:
        ch.insert(k, k)
    lengths = ch.chain_lengths()
    print(f"\nЦепочки: макс. длина {max(lengths)}, "
          f"средняя {sum(lengths) / len(lengths):.3f}, "
          f"пустых ячеек {lengths.count(0)} из {M}")

    # --- Кластеры при линейном пробировании ---
    oh = OpenHashTable()
    for k in keys:
        oh.insert(k, k)
    clusters = oh.cluster_lengths()
    if clusters:
        print(f"Кластеры: макс. длина {max(clusters)}, "
              f"число кластеров {len(clusters)}, "
              f"средняя длина {sum(clusters) / len(clusters):.2f}")
    else:
        print("Кластеров нет")

    # --- Графики ---
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # Гистограмма длин цепочек
    axes[0].hist(lengths, bins=range(0, max(lengths) + 2), align="left",
                 rwidth=0.8, color="steelblue")
    axes[0].set_xlabel("Длина цепочки")
    axes[0].set_ylabel("Число ячеек")
    axes[0].set_title("Распределение длин цепочек (метод цепочек)")
    axes[0].grid(True, alpha=0.3)

    # Гистограмма длин кластеров
    if clusters:
        axes[1].hist(clusters, bins=range(1, max(clusters) + 2), align="left",
                     rwidth=0.8, color="darkorange")
        axes[1].set_xlabel("Длина кластера")
        axes[1].set_ylabel("Число кластеров")
        axes[1].set_title("Распределение кластеров (линейное пробирование)")
        axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig("lr5_plot.png", dpi=150)
    plt.show()