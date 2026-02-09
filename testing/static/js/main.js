console.log("Anti-cheat is running");

document.addEventListener("visibilitychange", function() {
    if (document.hidden) {
        finishTest("Сіз басқа бетке өткеніңіз үшін тест аяқталды!");
    }
});

window.onblur = function() {
    finishTest("Экраннан шыққаныңыз үшін тест аяқталды!");
};

let submitted = false;
function finishTest(reason) {
    if (!submitted) {
        submitted = true;
        alert(reason);
        document.getElementById("examForm").submit();
    }
}