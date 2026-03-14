//===----------------------------------------------------------------------===//
//  MIT License.
//  Copyright (c) 2020-2026 The SLANG Authors.
//
//  Author: Anshuman Dhuliya (dhuliya@cse.iitb.ac.in)
//
//===----------------------------------------------------------------------===//
// The Util class has general purpose methods.
//===----------------------------------------------------------------------===//

#ifndef LLVM_SLANGUTIL_H
#define LLVM_SLANGUTIL_H

#include <string>
#include "llvm/Support/Process.h"

#define EXEC_NAME "slang"

#define SET_SRC_LOCATION_BIT_PTR(bitObject, srcLoc, name) \
    (bitObject)->set_##name##_line(srcLoc.line); \
    (bitObject)->set_##name##_col(srcLoc.col);

#define SET_SRC_LOCATION_BIT(bitObject, srcLoc, name) \
    (bitObject).set_##name##_line(srcLoc.line); \
    (bitObject).set_##name##_col(srcLoc.col);

#define COPY_SRC_LOCATION_BIT(destBitObject1, dest, srcBitObject2, src) \
    (destBitObject1)->set_##dest##_line((srcBitObject2)->##src##_line()); \
    (destBitObject1)->set_##dest##_col((srcBitObject2)->##src##_col());

#define EXTRACT_BITSRCLOC_OBJ(bitObject, name) \
    BitSrcLoc((bitObject)->##name##_line(), (bitObject)->##name##_col());

// TRACE < DEBUG < INFO < EVENT < ERROR < FATAL
#define SLANG_TRACE_LEVEL 10
#define SLANG_DEBUG_LEVEL 20
#define SLANG_INFO_LEVEL  30
#define SLANG_EVENT_LEVEL 40
#define SLANG_ERROR_LEVEL 50
#define SLANG_FATAL_LEVEL 60

// The macros for the five logging levels.
// TRACE < DEBUG < INFO < EVENT < ERROR < FATAL

#define SLANG_TRACE_GUARD(XX)                         \
    if (slang::Util::LogLevel <= SLANG_TRACE_LEVEL) { \
        XX;                                           \
    }

#define SLANG_DEBUG_GUARD(XX)                         \
    if (slang::Util::LogLevel <= SLANG_DEBUG_LEVEL) { \
        XX;                                           \
    }

#define SLANG_INFO_GUARD(XX)                          \
    if (slang::Util::LogLevel <= SLANG_INFO_LEVEL) {  \
        XX;                                           \
    }

#define SLANG_EVENT_GUARD(XX)                         \
    if (slang::Util::LogLevel <= SLANG_EVENT_LEVEL) { \
        XX;                                           \
    }

#define SLANG_ERROR_GUARD(XX)                         \
    if (slang::Util::LogLevel <= SLANG_ERROR_LEVEL) { \
        XX;                                           \
    }

#define SLANG_FATAL_GUARD(XX)                         \
    if (slang::Util::LogLevel <= SLANG_FATAL_LEVEL) { \
        XX;                                           \
    }

#define SLANG_TRACE(XX)                                                            \
    if (slang::Util::LogLevel <= SLANG_TRACE_LEVEL) {                              \
        llvm::errs() << "\n  " << slang::Util::getDateTimeString() << ": TRACE: (" \
                     << SLANG_TRACE_LEVEL << "):" << __FILE__ << ":" << __func__   \
                     << "():" << __LINE__ << ":\n"                                 \
                     << XX << "\n";                                                \
    }

#define SLANG_DEBUG(XX)                                                            \
    if (slang::Util::LogLevel <= SLANG_DEBUG_LEVEL) {                              \
        llvm::errs() << "\n  " << slang::Util::getDateTimeString() << ": DEBUG: (" \
                     << SLANG_DEBUG_LEVEL << "):" << __FILE__ << ":" << __func__   \
                     << "():" << __LINE__ << ":\n"                                 \
                     << XX << "\n";                                                \
    }

#define SLANG_INFO(XX)                                                             \
    if (slang::Util::LogLevel <= SLANG_INFO_LEVEL) {                               \
        llvm::errs() << "\n  " << slang::Util::getDateTimeString() << ": INFO:  (" \
                     << SLANG_INFO_LEVEL << "):" << __FILE__ << ":" << __func__    \
                     << "():" << __LINE__ << ":\n"                                 \
                     << XX << "\n";                                                \
    }

#define SLANG_EVENT(XX)                                                            \
    if (slang::Util::LogLevel <= SLANG_EVENT_LEVEL) {                              \
        llvm::errs() << "\n  " << slang::Util::getDateTimeString() << ": EVENT: (" \
                     << SLANG_EVENT_LEVEL << "):" << __FILE__ << ":" << __func__   \
                     << "():" << __LINE__ << ":\n"                                 \
                     << XX << "\n";                                                \
    }

#define SLANG_ERROR(XX)                                                            \
    if (slang::Util::LogLevel <= SLANG_ERROR_LEVEL) {                              \
        llvm::errs() << "\n  " << slang::Util::getDateTimeString() << ": ERROR: (" \
                     << SLANG_ERROR_LEVEL << "):" << __FILE__ << ":" << __func__   \
                     << "():" << __LINE__ << ":\n"                                 \
                     << XX << "\n";                                                \
    }

#define SLANG_FATAL(XX)                                                            \
    if (slang::Util::LogLevel <= SLANG_FATAL_LEVEL) {                              \
        llvm::errs() << "\n  " << slang::Util::getDateTimeString() << ": FATAL ("  \
                     << SLANG_FATAL_LEVEL << "):" << __FILE__ << ":" << __func__   \
                     << "():" << __LINE__ << ":\n"                                 \
                     << XX << "\n";                                                \
    }

namespace slang {
class Util {
    static uint32_t id;

  public:
    /** Get the current date-time string.
     *
     *  Mostly used for logging purposes.
     *
     * @return date-time in "%d-%m-%Y %H:%M:%S" format.
     */
    static std::string getDateTimeString();

    /** Read all contents of the given file.
     *
     * @return contents if successful.
     */
    static std::string readFromFile(std::string fileName);

    /** Append contents to the given fileName.
     *
     * @return zero if failed.
     */
    static int appendToFile(std::string fileName, std::string content);

    /** Write contents to the given fileName.
     *
     * @return zero if failed.
     */
    static int writeToFile(std::string fileName, std::string content);

    static uint32_t getNextUniqueId();
    static std::string getNextUniqueIdStr();

    static uint64_t double_to_u64(double d);
    static double u64_to_double(uint64_t u);

    /** The global level of logging.
     *
     *  Set logging level to SLANG_EVENT_LEVEL on deployment.
     * */
    static uint8_t LogLevel;
};
} // namespace slang

#endif // LLVM_SLANGUTIL_H