"use client";
import SnapPage from "../page";
import { Suspense } from "react";

export default function AlwaysClarifyPage() {
    return (
        <Suspense fallback={null}>
            <SnapPage />
        </Suspense>
    );
}
