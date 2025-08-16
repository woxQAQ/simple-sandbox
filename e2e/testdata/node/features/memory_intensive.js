console.log("Starting memory intensive test...");

// 尝试分配大量内存
let largeArray = [];
for (let i = 0; i < 1000000; i++) {
    largeArray.push(i * 2);
    if (i % 100000 === 0) {
        console.log(`Processed ${i} elements, array length: ${largeArray.length}`);
    }
}

// 创建一个大型对象
let largeObject = {};
for (let i = 0; i < 100000; i++) {
    largeObject[`key_${i}`] = `value_${i}`;
}

console.log(`Large object created with ${Object.keys(largeObject).length} properties`);

// 计算一些统计信息
let sum = largeArray.reduce((acc, val) => acc + val, 0);
let average = sum / largeArray.length;

console.log(`Array sum: ${sum}`);
console.log(`Array average: ${average}`);

console.log("Memory intensive test completed successfully");