/* SPDX-License-Identifier: GPL-3.0-or-later */
/* Native title ABI cannot use the payload SDK's ELF-loader-dependent libc shim.
 * Keep QR generator assertions active; an invariant violation traps this process.
 */
__attribute__((noreturn)) void __assert(const char *function, const char *file,
                                       int line, const char *expression) {
    (void)function; (void)file; (void)line; (void)expression;
    __builtin_trap();
}
