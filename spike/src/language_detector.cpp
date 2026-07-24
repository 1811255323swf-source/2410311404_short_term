#include <algorithm>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <regex>
#include <sstream>
#include <string>
#include <vector>

namespace {

constexpr std::size_t kMaxInputChars = 20000;

struct Score {
    int value{0};
    std::vector<std::string> evidence;
};

bool contains(const std::string& text, const std::string& token) {
    return text.find(token) != std::string::npos;
}

bool matches(const std::string& text, const std::string& pattern) {
    return std::regex_search(text, std::regex(pattern));
}

void add_feature(Score& score, int weight, const std::string& label) {
    score.value += weight;
    score.evidence.push_back(label);
}

Score score_cpp(const std::string& code) {
    Score score;
    if (contains(code, "#include")) {
        add_feature(score, 5, "cpp:#include");
    }
    if (matches(code, R"(\bint\s+main\s*\()")) {
        add_feature(score, 5, "cpp:int-main");
    }
    if (contains(code, "std::")) {
        add_feature(score, 4, "cpp:std-namespace");
    }
    if (matches(code, R"(\b(vector|string|map|unordered_map|set)\s*<)")) {
        add_feature(score, 3, "cpp:template-type");
    }
    if (std::count(code.begin(), code.end(), ';') >= 2 &&
        contains(code, "{") && contains(code, "}")) {
        add_feature(score, 2, "cpp:brace-semicolon-structure");
    }
    if (contains(code, "nullptr") ||
        (score.value >= 5 && contains(code, "->"))) {
        add_feature(score, 2, "cpp:pointer-syntax");
    }
    return score;
}

Score score_python(const std::string& code) {
    Score score;
    if (matches(code, R"((^|\n)\s*(async\s+)?def\s+[A-Za-z_]\w*\s*\([^\n]*\)\s*:)")) {
        add_feature(score, 5, "python:def-block");
    }
    if (matches(code, R"((^|\n)\s*(from\s+\S+\s+import|import\s+\S+))")) {
        add_feature(score, 4, "python:import-statement");
    }
    if (contains(code, "if __name__")) {
        add_feature(score, 5, "python:main-guard");
    }
    if (matches(code, R"(\b(None|True|False)\b)")) {
        add_feature(score, 2, "python:built-in-literal");
    }
    if (matches(code, R"((^|\n)\s*(for|while|if|elif|else|try|except|with|class)\b[^\n]*:)")) {
        add_feature(score, 3, "python:colon-block");
    }
    if (score.value >= 3 && contains(code, "\n    ") && contains(code, ":")) {
        add_feature(score, 2, "python:indented-block");
    }
    return score;
}

std::string json_array(const std::vector<std::string>& values) {
    std::ostringstream out;
    out << '[';
    for (std::size_t index = 0; index < values.size(); ++index) {
        if (index > 0) {
            out << ',';
        }
        out << '"' << values[index] << '"';
    }
    out << ']';
    return out.str();
}

bool is_blank(const std::string& text) {
    return std::all_of(text.begin(), text.end(), [](unsigned char value) {
        return std::isspace(value) != 0;
    });
}

}  // namespace

int main(int argc, char* argv[]) {
    if (argc != 2) {
        std::cerr << "usage: language_detector <code-file>\n";
        return 2;
    }

    std::ifstream input(argv[1], std::ios::binary);
    if (!input) {
        std::cerr << "cannot read input file\n";
        return 2;
    }

    std::ostringstream buffer;
    buffer << input.rdbuf();
    const std::string code = buffer.str();

    if (code.empty() || is_blank(code)) {
        std::cout << R"({"error":"empty_code","detected_language":"unknown"})" << '\n';
        return 2;
    }
    if (code.size() > kMaxInputChars) {
        std::cout << R"({"error":"code_too_large","detected_language":"unknown"})" << '\n';
        return 2;
    }

    const Score cpp = score_cpp(code);
    const Score python = score_python(code);
    const int maximum = std::max(cpp.value, python.value);
    const int difference = std::abs(cpp.value - python.value);

    std::string language = "unknown";
    std::vector<std::string> evidence;
    double confidence = std::min(0.79, maximum / 10.0);

    if (maximum >= 5 && difference >= 3) {
        const bool is_cpp = cpp.value > python.value;
        language = is_cpp ? "cpp" : "python";
        evidence = is_cpp ? cpp.evidence : python.evidence;
        confidence = std::min(0.99, 0.75 + difference * 0.02);
    }

    std::cout << std::fixed << std::setprecision(2)
              << "{\"detected_language\":\"" << language
              << "\",\"confidence\":" << confidence
              << ",\"cpp_score\":" << cpp.value
              << ",\"python_score\":" << python.value
              << ",\"detection_evidence\":" << json_array(evidence)
              << "}" << '\n';
    return 0;
}
