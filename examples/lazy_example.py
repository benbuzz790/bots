"""Example demonstrating the @lazy decorator functionality.
WARNING: DEPRECATED - The @lazy decorator has been moved to a separate package.
This example is kept for reference, but the @lazy decorator is no longer
part of the bots framework. It has been extracted to the lazy-impl package.
To use lazy decorators:
1. Install the lazy-impl package: pip install lazy-impl
2. Import from lazy_impl instead of bots:
   from lazy_impl import lazy
For more information, see: https://github.com/your-org/lazy-impl
"""

# Original example (commented out - update imports to use lazy_impl):
# from lazy_impl import lazy  # Changed from: from bots import lazy
#
# @lazy("Sort using a funny algorithm. Name variables like a clown.")
# def sort(arr: list[int]) -> list[int]:
#     pass
if __name__ == "__main__":
    print("WARNING: This example requires the lazy-impl package.")
    print("Install it with: pip install lazy-impl")
    print("Then update the import: from lazy_impl import lazy")
    # Uncomment after installing lazy-impl:
    # result = sort([1, 2, 3, 4, 5, 0])
    # print(f"Sorted array: {result}")
