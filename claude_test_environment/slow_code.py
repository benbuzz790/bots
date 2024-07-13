
    import time
    def slow_function(n):
        result = []
        for i in range(n):
            result.append(i)
            time.sleep(0.01)
        return result
    def process_data(data):
        result = []
        for item in data:
            result.append(item ** 2)
        return result
    def main():
        data = slow_function(100)
        processed_data = process_data(data)
        print(f"Processed {len(processed_data)} items")
    if __name__ == "__main__":
        main()
        