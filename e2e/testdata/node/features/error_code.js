console.log("Before error");
throw new Error("This is a test error");
console.log("After error");  // 这行不会执行