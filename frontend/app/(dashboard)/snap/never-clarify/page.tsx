"use client";
import SnapPage from "../page";
import { Suspense } from "react";

export default function NeverClarifyPage() {
    return (
        <Suspense fallback={null}>
            <SnapPage />
        </Suspense>
    );
}
